import re
import ast
import math
from typing import Dict, List, Optional, Any

class StringDecoder:
    def __init__(self):
        self.pattern_cache = {}
        self.decoded_strings = []
        
    def decode_escapes(self, text: str) -> str:
        def replace_octal(match):
            num = match.group(1)
            return chr(int(num, 8))
        
        def replace_hex(match):
            num = match.group(1)
            return chr(int(num, 16))
        
        replacements = [
            (r'\\([0-7]{1,3})', replace_octal),
            (r'\\x([0-9a-fA-F]{2})', replace_hex),
            (r'\\n', '\n'),
            (r'\\r', '\r'),
            (r'\\t', '\t'),
            (r'\\"', '"'),
            (r"\\'", "'"),
            (r'\\\\', '\\')
        ]
        
        for pattern, replacement in replacements:
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = text.replace(pattern, replacement)
                
        return text
    
    def analyze_expression(self, expr: str) -> Any:
        try:
            expr = expr.strip()
            
            if expr.startswith('"') and expr.endswith('"'):
                return self.decode_escapes(expr[1:-1])
            
            if expr.startswith("'") and expr.endswith("'"):
                return self.decode_escapes(expr[1:-1])
            
            tree = ast.parse(expr, mode='eval')
            
            def eval_node(node):
                if isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    left = eval_node(node.left)
                    right = eval_node(node.right)
                    
                    if isinstance(node.op, ast.Add):
                        return left + right
                    elif isinstance(node.op, ast.Sub):
                        return left - right
                    elif isinstance(node.op, ast.Mult):
                        return left * right
                    elif isinstance(node.op, ast.Div):
                        return left / right if right != 0 else 0
                
                return None
            
            return eval_node(tree.body)
            
        except:
            return None
    
    def find_string_tables(self, content: str) -> List[Dict]:
        patterns = [
            r'local\s+(\w+)\s*=\s*\{([^}]+)\}',
            r'(\w+)\s*=\s*\{([^}]+)\}',
            r'table\.create.*?\{([^}]+)\}'
        ]
        
        results = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                table_name = match.group(1) if match.groups() > 1 else "unnamed"
                table_content = match.group(2) if match.groups() > 1 else match.group(1)
                
                if '"' in table_content or "'" in table_content:
                    results.append({
                        'name': table_name,
                        'content': table_content,
                        'type': 'string_table'
                    })
        
        return results
    
    def process_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        analysis = {
            'file': filepath,
            'size': len(content),
            'tables_found': self.find_string_tables(content),
            'strings': [],
            'operations': []
        }
        
        string_matches = re.finditer(r'["\'](.*?)["\']', content)
        for match in string_matches:
            decoded = self.decode_escapes(match.group(0))
            analysis['strings'].append({
                'original': match.group(0),
                'decoded': decoded,
                'position': match.start()
            })
        
        return analysis

class PatternDetector:
    def __init__(self):
        self.patterns = {
            'base64': r'[A-Za-z0-9+/]+={0,2}',
            'hex': r'[0-9A-Fa-f]{8,}',
            'obfuscated_call': r'\w+\([^)]*\)',
            'encoded_array': r'\[[^\]]+\]'
        }
    
    def detect(self, content: str) -> List[Dict]:
        detections = []
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.group()) > 6:
                    detections.append({
                        'type': pattern_name,
                        'match': match.group(),
                        'position': match.start()
                    })
        
        return detections
