import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from string_analyzer import StringDecoder, PatternDetector
    from script_processor import ScriptProcessor
except ImportError:
    print("Required modules not found.")
    sys.exit(1)

class AnalysisOrchestrator:
    def __init__(self):
        self.string_decoder = StringDecoder()
        self.pattern_detector = PatternDetector()
        self.script_processor = ScriptProcessor()
        self.analysis_start = datetime.now()
        
    def process_files(self, input_path, mode="full"):
        path = Path(input_path)
        files = []
        
        if path.is_file():
            files = [str(path)]
        elif path.is_dir():
            for file_path in path.rglob('*.lua'):
                files.append(str(file_path))
        
        results = []
        for filepath in files:
            print(f"Analyzing: {filepath}")
            result = self.analyze_file(filepath, mode)
            results.append(result)
        
        return results
    
    def analyze_file(self, filepath, mode):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {'file': filepath, 'error': str(e)}
        
        result = {
            'file': filepath,
            'size': len(content),
            'mode': mode
        }
        
        if mode in ["strings", "full"]:
            result['strings'] = self.string_decoder.extract_strings(content)
        
        if mode in ["patterns", "full"]:
            result['patterns'] = self.pattern_detector.scan(content)
        
        return result

def main():
    parser = argparse.ArgumentParser(description="Lua Analysis Tool")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--mode", choices=["strings", "patterns", "full"], default="full")
    parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Path '{args.input}' not found")
        sys.exit(1)
    
    orchestrator = AnalysisOrchestrator()
    results = orchestrator.process_files(args.input, args.mode)
    
    print(f"\nProcessed {len(results)} file(s)")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
import
