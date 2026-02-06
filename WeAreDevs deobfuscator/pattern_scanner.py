import re

class PatternScanner:
    def __init__(self):
        self.registered_patterns = {}
        self.scan_results = {}
    
    def register_pattern_type(self, name, pattern, weight_value=1):
        self.registered_patterns[name] = {
            'pattern_string': pattern,
            'weight_value': weight_value,
            'compiled_pattern': re.compile(pattern, re.MULTILINE | re.DOTALL)
        }
    
    def scan_text_content(self, text_input):
        results = {}
        
        for pattern_name, pattern_data in self.registered_patterns.items():
            pattern_object = pattern_data['compiled_pattern']
            found_matches = pattern_object.findall(text_input)
            
            if found_matches:
                results[pattern_name] = {
                    'match_count': len(found_matches),
                    'pattern_weight': pattern_data['weight_value'],
                    'total_score': len(found_matches) * pattern_data['weight_value'],
                    'sample_matches': found_matches[:3] if found_matches else []
                }
        
        return results
    
    def load_default_patterns(self):
        self.register_pattern_type('base64_pattern', r'[A-Za-z0-9+/]+={0,2}', 2)
        self.register_pattern_type('hex_pattern', r'0x[0-9A-Fa-f]+', 1)
        self.register_pattern_type('data_table', r'local\s+\w+\s*=\s*\{[^}]+\}', 3)
        self.register_pattern_type('function_call', r'\w+\([^)]*\)', 1)
        self.register_pattern_type('concat_operation', r'table\.concat\s*\([^)]+\)', 2)
        self.register_pattern_type('char_function', r'string\.char\([^)]+\)', 2)
        self.register_pattern_type('bit_operation', r'bit32\.[a-z]+\([^)]+\)', 2)
        self.register_pattern_type('load_function', r'loadstring\s*\([^)]+\)', 3)
        self.register_pattern_type('env_access', r'getfenv|setfenv|getgenv', 3)
        self.register_pattern_type('numeric_sequence', r'\b\d{4,}\b', 1)
    
    def analyze_target_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            
            self.load_default_patterns()
            detection_data = self.scan_text_content(file_content)
            
            total_score_value = sum(item['total_score'] for item in detection_data.values())
            
            analysis_data = {
                'target_file': file_path,
                'content_size': len(file_content),
                'detection_data': detection_data,
                'total_score_value': total_score_value,
                'risk_assessment': self.assess_risk_level(total_score_value)
            }
            
            return analysis_data
            
        except Exception as error_instance:
            return {
                'target_file': file_path,
                'error_message': str(error_instance)
            }
    
    def assess_risk_level(self, score_value):
        if score_value > 50:
            return "High"
        elif score_value > 20:
            return "Medium"
        elif score_value > 5:
            return "Low"
        else:
            return "Minimal"
    
    def create_detection_report(self, analysis_data):
        if 'error_message' in analysis_data:
            return f"Error: {analysis_data['error_message']}"
        
        report_lines = []
        report_lines.append(f"Target File: {analysis_data['target_file']}")
        report_lines.append(f"Content Size: {analysis_data['content_size']} characters")
        report_lines.append(f"Detection Score: {analysis_data['total_score_value']}")
        report_lines.append(f"Risk Assessment: {analysis_data['risk_assessment']}")
        
        report_lines.append("\nPattern Detections:")
        for pattern_name, detection_info in analysis_data['detection_data'].items():
            report_lines.append(f"  {pattern_name}: {detection_info['match_count']} matches (score: {detection_info['total_score']})")
        
        return '\n'.join(report_lines)
