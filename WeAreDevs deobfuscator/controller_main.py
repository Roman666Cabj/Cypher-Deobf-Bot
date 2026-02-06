import sys
import json
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: python controller_main.py <lua_file> [--mode=<mode>] [--output=<file>]")
        print("Available modes: strings, patterns, execute, full")
        sys.exit(1)
    
    target_file = sys.argv[1]
    selected_mode = "full"
    output_target = None
    
    for argument in sys.argv[2:]:
        if argument.startswith("--mode="):
            selected_mode = argument.split("=")[1]
        elif argument.startswith("--output="):
            output_target = argument.split("=")[1]
    
    try:
        from deobfuscator_core import Deobfuscator
        from pattern_scanner import PatternScanner
        from execution_engine import ExecutionEngine
    except ImportError as import_error:
        print(f"Import Error: {import_error}")
        print("Required files: deobfuscator_core.py, pattern_scanner.py, execution_engine.py")
        sys.exit(1)
    
    print(f"Target: {target_file}")
    print(f"Mode: {selected_mode}")
    print("-" * 50)
    
    analysis_results = {
        'target_file': target_file,
        'analysis_timestamp': datetime.now().isoformat(),
        'selected_mode': selected_mode
    }
    
    if selected_mode in ["strings", "full"]:
        print("\n[1/3] Processing strings...")
        string_processor = Deobfuscator()
        string_analysis = string_processor.analyze_script(target_file)
        analysis_results['string_analysis'] = string_analysis
        
        if 'decrypted_strings' in string_analysis:
            string_count = len(string_analysis['decrypted_strings'])
            print(f"  Decrypted strings: {string_count}")
            for index, string_value in enumerate(string_analysis['decrypted_strings'][:5]):
                preview_text = string_value[:40] + "..." if len(string_value) > 40 else string_value
                print(f"    {index+1}. {preview_text}")
    
    if selected_mode in ["patterns", "full"]:
        print("\n[2/3] Scanning patterns...")
        pattern_scanner = PatternScanner()
        pattern_analysis = pattern_scanner.analyze_target_file(target_file)
        analysis_results['pattern_analysis'] = pattern_analysis
        
        if 'detection_data' in pattern_analysis:
            score_value = pattern_analysis.get('total_score_value', 0)
            risk_level = pattern_analysis.get('risk_assessment', 'Unknown')
            print(f"  Detection Score: {score_value}")
            print(f"  Risk Level: {risk_level}")
            
            detection_items = pattern_analysis.get('detection_data', {})
            for pattern_name, detection_info in list(detection_items.items())[:5]:
                print(f"    {pattern_name}: {detection_info['match_count']} occurrences")
    
    if selected_mode in ["execute", "full"]:
        print("\n[3/3] Executing code...")
        execution_engine = ExecutionEngine(max_time=10)
        execution_analysis = execution_engine.process_script_file(target_file)
        analysis_results['execution_analysis'] = execution_analysis
        
        exec_details = execution_analysis.get('execution_details', {})
        print(f"  Success: {exec_details.get('successful', False)}")
        print(f"  Duration: {exec_details.get('duration', 0):.3f}s")
        
        if exec_details.get('output_text'):
            output_preview = exec_details['output_text'][:200]
            if len(exec_details['output_text']) > 200:
                output_preview += "..."
            print(f"  Output: {output_preview}")
    
    print("\n" + "=" * 50)
    print("Analysis Completed")
    
    if output_target:
        with open(output_target, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_target}")

if __name__ == "__main__":
    main()
