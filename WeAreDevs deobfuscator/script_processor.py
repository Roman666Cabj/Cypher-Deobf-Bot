import subprocess
import tempfile
import os
import hashlib

class ScriptProcessor:
    def process_script(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metrics = {
                'size': len(content),
                'lines': content.count('\n') + 1,
                'hash': hashlib.md5(content.encode()).hexdigest()
            }
            
            return {
                'metrics': metrics,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def execute_lua(self, code):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['lua', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Timeout'}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path) 
