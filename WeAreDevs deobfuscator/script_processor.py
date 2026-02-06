import subprocess
import tempfile
import os
import json
import hashlib
from pathlib import Path

class ScriptProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lua_analyzer_")
        self.results = {}
        
    def generate_harness(self, lua_code: str, mode: str = "analysis") -> str:
        harness_template = """
local analysis_mode = "{mode}"
local start_time = os.clock()

local function log_event(event_type, data)
    print(string.format("[ANALYSIS] %s: %s", event_type, data))
end

local execution_env = {{}}
setmetatable(execution_env, {{
    __index = function(t, k)
        if k == "print" then
            return function(...)
                local args = {{...}}
                local output = table.concat(args, "\\t")
                log_event("PRINT", output)
            end
        end
        return nil
    end
}})

{user_code}

local execution_time = os.clock() - start_time
log_event("COMPLETION", string.format("Execution time: %.3f seconds", execution_time))
"""
        
        return harness_template.format(mode=mode, user_code=lua_code)
    
    def execute_with_lua(self, lua_code: str) -> Dict:
        temp_file = os.path.join(self.temp_dir, "analysis.lua")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(lua_code)
        
        try:
            result = subprocess.run(
                ['lua', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Execution timeout',
                'returncode': -1
            }
    
    def extract_functions(self, content: str) -> List[Dict]:
        function_patterns = [
            r'function\s+(\w+)\(([^)]*)\)',
            r'local\s+function\s+(\w+)\(([^)]*)\)',
            r'(\w+)\s*=\s*function\(([^)]*)\)'
        ]
        
        functions = []
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                functions.append({
                    'name': match.group(1),
                    'params': match.group(2).split(',') if match.group(2) else [],
                    'signature': match.group(0)
                })
        
        return functions
    
    def calculate_metrics(self, content: str) -> Dict:
        lines = content.split('\n')
        
        return {
            'line_count': len(lines),
            'char_count': len(content),
            'function_count': len(self.extract_functions(content)),
            'hash_md5': hashlib.md5(content.encode()).hexdigest(),
            'hash_sha256': hashlib.sha256(content.encode()).hexdigest(),
            'avg_line_length': sum(len(line) for line in lines) / max(len(lines), 1)
        }
    
    def process_script(self, filepath: str) -> Dict:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        metrics = self.calculate_metrics(content)
        
        harness = self.generate_harness(content, "full_analysis")
        execution_result = self.execute_with_lua(harness)
        
        analysis_result = {
            'file': filepath,
            'metrics': metrics,
            'functions': self.extract_functions(content),
            'execution': execution_result,
            'analysis_timestamp': os.time()
        }
        
        self.results[filepath] = analysis_result
        return analysis_result
    
    def save_report(self, output_path: str):
        report = {
            'processor_version': '2.0.0',
            'analysis_date': os.date(),
            'processed_files': len(self.results),
            'results': self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return output_path
