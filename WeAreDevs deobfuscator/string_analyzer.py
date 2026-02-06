# string_analyzer.py
import re

class StringDecoder:
    def decode_escapes(self, text):
        replacements = {
            r'\\n': '\n',
            r'\\r': '\r',
            r'\\t': '\t',
            r'\\"': '"',
            r"\\'": "'",
            r'\\\\': '\\'
        }
        
        for pattern, replacement in replacements.items():
            text = text.replace(pattern, replacement)
        
        def replace_octal(match):
            return chr(int(match.group(1)))
        
        text = re.sub(r'\\(\d{1,3})', replace_octal, text)
        
        return text
    
    def extract_strings(self, content):
        strings = []
        
        string_patterns = [
            r'"([^"\\]*(\\.[^"\\]*)*)"',
            r"'([^'\\]*(\\.[^'\\]*)*)'"
        ]
        
        for pattern in string_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                original = match.group(0)
                decoded = self.decode_escapes(original)
                strings.append({
                    'original': original,
                    'decoded': decoded,
                    'position': match.start()
                })
        
        return strings

class PatternDetector:
    def scan(self, content):
        patterns = {
            'base64': r'[A-Za-z0-9+/]+={0,2}',
            'hex': r'0x[0-9A-Fa-f]+',
            'number': r'\b\d+\b'
        }
        
        results = {}
        for name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                results[name] = len(matches)
        
        return results
