#!/usr/bin/env python3
"""
TOP 10 PROJECTS — COMBINED CODE + DOCS REPORT
Generates a snapshot of both codebase and markdown base for each project
"""

import yaml
import os
import glob
from pathlib import Path
from datetime import datetime

def count_files(path_patterns, extensions):
    """Count files matching patterns and extensions."""
    count = 0
    for pattern in path_patterns:
        expanded = os.path.expanduser(pattern)
        for ext in extensions:
            files = glob.glob(f"{expanded}/**/*{ext}", recursive=True)
            count += len(files)
    return count

def count_lines(path_patterns, extensions):
    """Count total lines in files."""
    total_lines = 0
    for pattern in path_patterns:
        expanded = os.path.expanduser(pattern)
        for ext in extensions:
            for filepath in glob.glob(f"{expanded}/**/*{ext}", recursive=True):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
    return total_lines

def generate_report():
    """Generate combined code + docs report for TOP 10 projects."""
    config_path = Path.home() / "DHARMIC_GODEL_CLAW/config/top_10_projects.yaml"
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    tracking = config.get('tracking', {})
    code_exts = tracking.get('code_extensions', ['.py'])
    doc_exts = tracking.get('doc_extensions', ['.md'])
    project_tracking = tracking.get('project_paths', {})
    
    print("="*80)
    print(f"TOP 10 PROJECTS — CODE + DOCS SNAPSHOT — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    for pid, paths in project_tracking.items():
        code_paths = paths.get('code_paths', [])
        doc_paths = paths.get('doc_paths', [])
        
        # Count code
        code_files = count_files(code_paths, code_exts)
        code_lines = count_lines(code_paths, code_exts) if code_paths else 0
        
        # Count docs
        doc_files = count_files(doc_paths, doc_exts)
        doc_lines = count_lines(doc_paths, doc_exts) if doc_paths else 0
        
        # Ratio
        ratio = code_lines / doc_lines if doc_lines > 0 else 0
        
        print(f"\n{pid}:")
        print(f"  📁 Code:  {code_files:4d} files | {code_lines:8,d} lines")
        print(f"  📄 Docs:  {doc_files:4d} files | {doc_lines:8,d} lines")
        print(f"  📊 Ratio: {ratio:.2f} (code/doc)")
    
    print("\n" + "="*80)
    print("GOAL: Keep both code AND docs advancing — no orphan files")
    print("="*80)

if __name__ == "__main__":
    generate_report()
