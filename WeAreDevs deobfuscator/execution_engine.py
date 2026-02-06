import subprocess
import tempfile
import os
import time

class ExecutionEngine:
    def __init__(self, max_time=10):
        self.max_execution_time = max_time
        self.execution_log = []
    
    def create_execution_environment(self, code_content):
        environment_code = """
local start_moment = os.clock()

local function monitor_output(...)
    local output_args = {...}
    local combined_output = ""
    for index, value in ipairs(output_args) do
        combined_output = combined_output .. tostring(value)
        if index < #output_args then
            combined_output = combined_output .. "\\t"
        end
    end
    print("[EXECUTION OUTPUT] " .. combined_output)
end

local original_print = print
print = monitor_output

""" + code_content + """

print = original_print
local end_moment = os.clock()
print(string.format("[EXECUTION COMPLETE] Duration: %.3f seconds", end_moment - start_moment))
"""
        return environment_code
    
    def execute_code_safely(self, lua_code, use_environment=True):
        if use_environment:
            lua_code = self.create_execution_environment(lua_code)
        
        temporary_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(lua_code)
                temporary_file = f.name
            
            start_time = time.time()
            
            execution_result = subprocess.run(
                ['lua', temporary_file],
                capture_output=True,
                text=True,
                timeout=self.max_execution_time
            )
            
            elapsed_time = time.time() - start_time
            
            result_record = {
                'successful': execution_result.returncode == 0,
                'output_text': execution_result.stdout,
                'error_text': execution_result.stderr,
                'exit_code': execution_result.returncode,
                'duration': elapsed_time,
                'timed_out': False
            }
            
            self.execution_log.append(result_record)
            return result_record
            
        except subprocess.TimeoutExpired:
            result_record = {
                'successful': False,
                'output_text': '',
                'error_text': 'Execution timeout reached',
                'exit_code': -1,
                'duration': self.max_execution_time,
                'timed_out': True
            }
            self.execution_log.append(result_record)
            return result_record
            
        except Exception as error_instance:
            result_record = {
                'successful': False,
                'output_text': '',
                'error_text': str(error_instance),
                'exit_code': -1,
                'duration': 0,
                'timed_out': False,
                'error_occurred': True
            }
            self.execution_log.append(result_record)
            return result_record
            
        finally:
            if temporary_file and os.path.exists(temporary_file):
                try:
                    os.remove(temporary_file)
                except:
                    pass
    
    def process_script_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            
            execution_result = self.execute_code_safely(file_content)
            
            analysis_result = {
                'target_file': file_path,
                'content_size': len(file_content),
                'execution_details': execution_result,
                'log_entries': len(self.execution_log)
            }
            
            return analysis_result
            
        except Exception as error_instance:
            return {
                'target_file': file_path,
                'error_message': str(error_instance)
            }
    
    def get_execution_summary(self):
        if not self.execution_log:
            return "No execution records available"
        
        successful_count = sum(1 for record in self.execution_log if record['successful'])
        total_count = len(self.execution_log)
        
        summary_data = {
            'total_executions': total_count,
            'successful_executions': successful_count,
            'success_percentage': (successful_count / total_count * 100) if total_count > 0 else 0,
            'average_duration': sum(r['duration'] for r in self.execution_log) / total_count if total_count > 0 else 0,
            'timeout_count': sum(1 for r in self.execution_log if r.get('timed_out', False))
        }
        
        return summary_data
