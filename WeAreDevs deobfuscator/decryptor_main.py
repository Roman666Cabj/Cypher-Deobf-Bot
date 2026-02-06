import re
import base64
import codecs
import struct

class Deobfuscator:
    def __init__(self):
        self.decrypted_data = {}
        self.decryption_keys = {}
    
    def process_base64(self, encoded_data):
        try:
            missing_padding = len(encoded_data) % 4
            if missing_padding:
                encoded_data += '=' * (4 - missing_padding)
            return base64.b64decode(encoded_data).decode('utf-8', errors='ignore')
        except:
            return encoded_data
    
    def process_hex_data(self, hex_data):
        try:
            if hex_data.startswith('0x'):
                hex_data = hex_data[2:]
            hex_data = re.sub(r'[^0-9A-Fa-f]', '', hex_data)
            if len(hex_data) % 2 != 0:
                hex_data = '0' + hex_data
            return bytes.fromhex(hex_data).decode('utf-8', errors='ignore')
        except:
            return hex_data
    
    def process_octal_data(self, octal_data):
        def replace_octal(match):
            return chr(int(match.group(1), 8))
        return re.sub(r'\\(\d{1,3})', replace_octal, octal_data)
    
    def apply_xor_cipher(self, input_data, cipher_key):
        try:
            output_chars = []
            key_bytes = str(cipher_key).encode() if not isinstance(cipher_key, bytes) else cipher_key
            
            for i, char_val in enumerate(input_data):
                key_val = key_bytes[i % len(key_bytes)]
                if isinstance(char_val, str):
                    output_chars.append(chr(ord(char_val) ^ key_val))
                else:
                    output_chars.append(chr(char_val ^ key_val))
            return ''.join(output_chars)
        except:
            return input_data
    
    def locate_data_tables(self, script_content):
        found_tables = []
        
        table_pattern = r'local\s+(\w+)\s*=\s*\{(.*?)\}'
        
        for table_match in re.finditer(table_pattern, script_content, re.DOTALL):
            table_identifier = table_match.group(1)
            table_elements = table_match.group(2)
            
            element_list = []
            current_position = 0
            
            while current_position < len(table_elements):
                if table_elements[current_position] in ['"', "'"]:
                    quote_symbol = table_elements[current_position]
                    element_end = current_position + 1
                    
                    while element_end < len(table_elements):
                        if table_elements[element_end] == quote_symbol and table_elements[element_end-1] != '\\':
                            break
                        element_end += 1
                    
                    if element_end < len(table_elements):
                        raw_element = table_elements[current_position + 1:element_end]
                        processed_element = self.process_string_escapes(raw_element)
                        element_list.append(processed_element)
                        current_position = element_end + 1
                        continue
                current_position += 1
            
            if element_list:
                found_tables.append({
                    'name': table_identifier,
                    'elements': element_list
                })
        
        return found_tables
    
    def process_string_escapes(self, raw_string):
        escape_replacements = {
            r'\\n': '\n',
            r'\\r': '\r',
            r'\\t': '\t',
            r'\\"': '"',
            r"\\'": "'",
            r'\\\\': '\\',
            r'\\a': '\a',
            r'\\b': '\b',
            r'\\f': '\f',
            r'\\v': '\v'
        }
        
        def replace_hex(match):
            return chr(int(match.group(1), 16))
        
        for pattern, replacement in escape_replacements.items():
            raw_string = raw_string.replace(pattern, replacement)
        
        raw_string = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex, raw_string)
        
        return raw_string
    
    def find_encryption_functions(self, script_content):
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)\s*local\s+.*string\.char',
            r'local\s+function\s+(\w+)\s*\([^)]*\)\s*.*bit32\.',
            r'(\w+)\s*=\s*function\s*\([^)]*\)\s*.*table\.concat'
        ]
        
        encryption_functions = []
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, script_content, re.DOTALL)
            for match in matches:
                if match.group(1):
                    function_start = match.start()
                    function_end = script_content.find('end', function_start)
                    if function_end != -1:
                        function_body = script_content[function_start:function_end + 3]
                        encryption_functions.append({
                            'name': match.group(1),
                            'body': function_body
                        })
        
        return encryption_functions
    
    def extract_cipher_mapping(self, script_content):
        mapping_pattern = r'local\s+(\w+)\s*=\s*\{(.*?)\}'
        
        for match in re.finditer(mapping_pattern, script_content, re.DOTALL):
            mapping_content = match.group(2)
            
            if '=' in mapping_content and mapping_content.count('=') > 10:
                mapping_dict = {}
                
                elements = re.findall(r'\["([^"]+)"\]\s*=\s*(\d+)', mapping_content)
                for key, value in elements:
                    mapping_dict[key] = int(value)
                
                if len(mapping_dict) > 30:
                    return mapping_dict
        
        return {}
    
    def reconstruct_strings(self, encrypted_strings, cipher_map):
        reconstructed = []
        
        for enc_string in encrypted_strings:
            if not isinstance(enc_string, str):
                reconstructed.append("")
                continue
            
            byte_buffer = bytearray()
            accumulator = 0
            position_counter = 0
            
            for char in enc_string:
                if char in cipher_map:
                    char_value = cipher_map[char]
                    accumulator = (accumulator << 6) | char_value
                    position_counter += 1
                    
                    if position_counter == 4:
                        byte_buffer.append((accumulator >> 16) & 0xFF)
                        byte_buffer.append((accumulator >> 8) & 0xFF)
                        byte_buffer.append(accumulator & 0xFF)
                        accumulator = 0
                        position_counter = 0
                elif char == '=':
                    if position_counter == 3:
                        byte_buffer.append((accumulator >> 16) & 0xFF)
                        byte_buffer.append((accumulator >> 8) & 0xFF)
                    elif position_counter == 2:
                        byte_buffer.append((accumulator >> 16) & 0xFF)
                    break
            
            try:
                decoded_string = byte_buffer.decode('utf-8', errors='replace')
                reconstructed.append(decoded_string)
            except:
                reconstructed.append("[Binary Data]")
        
        return reconstructed
    
    def analyze_script(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            script_data = f.read()
        
        data_tables = self.locate_data_tables(script_data)
        cipher_mapping = self.extract_cipher_mapping(script_data)
        encryption_functions = self.find_encryption_functions(script_data)
        
        final_strings = []
        
        for table in data_tables:
            if cipher_mapping and len(cipher_mapping) > 30:
                decrypted = self.reconstruct_strings(table['elements'], cipher_mapping)
                final_strings.extend(decrypted)
            else:
                for element in table['elements']:
                    processed = self.process_string_escapes(element)
                    final_strings.append(processed)
        
        return {
            'script_file': file_path,
            'data_tables_found': len(data_tables),
            'cipher_mapping_size': len(cipher_mapping),
            'encryption_functions': len(encryption_functions),
            'decrypted_strings': final_strings
        }
    
    def generate_output(self, analysis_data):
        output_lines = []
        
        output_lines.append(f"Script: {analysis_data['script_file']}")
        output_lines.append(f"Data Tables: {analysis_data['data_tables_found']}")
        output_lines.append(f"Cipher Mapping Entries: {analysis_data['cipher_mapping_size']}")
        output_lines.append(f"Encryption Functions: {analysis_data['encryption_functions']}")
        
        output_lines.append("\nDecrypted Strings:")
        for idx, string_value in enumerate(analysis_data['decrypted_strings']):
            if string_value and len(string_value.strip()) > 0:
                preview = string_value[:100] + "..." if len(string_value) > 100 else string_value
                output_lines.append(f"  [{idx}] {preview}")
        
        return '\n'.join(output_lines)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python deobfuscator_core.py <lua_file>")
        sys.exit(1)
    
    deobf = Deobfuscator()
    results = deobf.analyze_script(sys.argv[1])
    output = deobf.generate_output(results)
    print(output) 
