import sys
import argparse
from datetime import datetime
from string_analyzer import StringDecoder, PatternDetector
from script_processor import ScriptProcessor

class AnalysisOrchestrator:
    def __init__(self):
        self.string_decoder = StringDecoder()
        self.pattern_detector = PatternDetector()
        self.script_processor = ScriptProcessor()
        self.analysis_start = datetime.now()
        
    def run_file_analysis(self, filepath: str, mode: str = "full") -> Dict:
        results = {
            'file': filepath,
            'analysis_mode': mode,
            'string_analysis': None,
            'pattern_detection': None,
            'execution_analysis': None
        }
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if mode in ["strings", "full"]:
            results['string_analysis'] = self.string_decoder.process_file(filepath)
        
        if mode in ["patterns", "full"]:
            results['pattern_detection'] = self.pattern_detector.detect(content)
        
        if mode in ["execute", "full"]:
            results['execution_analysis'] = self.script_processor.process_script(filepath)
        
        return results
    
    def generate_summary(self, analysis_results: List[Dict]) -> Dict:
        total_files = len(analysis_results)
        total_strings = 0
        total_patterns = 0
        
        for result in analysis_results:
            if result.get('string_analysis'):
                total_strings += len(result['string_analysis'].get('strings', []))
            if result.get('pattern_detection'):
                total_patterns += len(result['pattern_detection'])
        
        return {
            'total_files': total_files,
            'total_strings': total_strings,
            'total_patterns': total_patterns,
            'analysis_duration': str(datetime.now() - self.analysis_start),
            'orchestrator_version': '3.0.0'
        }

def main():
    parser = argparse.ArgumentParser(description="Advanced Lua Script Analysis Framework")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--mode", choices=["strings", "patterns", "execute", "full"], 
                       default="full", help="Analysis mode")
    parser.add_argument("--output", help="Output report file")
    
    args = parser.parse_args()
    
    orchestrator = AnalysisOrchestrator()
    
    import os
    files_to_process = []
    
    if os.path.isfile(args.input):
        files_to_process.append(args.input)
    elif os.path.isdir(args.input):
        for root, dirs, files in os.walk(args.input):
            for file in files:
                if file.endswith('.lua'):
                    files_to_process.append(os.path.join(root, file))
    
    print(f"Processing {len(files_to_process)} file(s)...")
    
    all_results = []
    for filepath in files_to_process:
        print(f"Analyzing: {filepath}")
        result = orchestrator.run_file_analysis(filepath, args.mode)
        all_results.append(result)
    
    summary = orchestrator.generate_summary(all_results)
    
    if args.output:
        import json
        final_report = {
            'summary': summary,
            'detailed_results': all_results
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to: {args.output}")
    
    print("Analysis complete.")
    print(f"Duration: {summary['analysis_duration']}")
    print(f"Files processed: {summary['total_files']}")

if __name__ == "__main__":
    main()
