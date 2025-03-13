#!/usr/bin/env python
"""
Script to run mypy type checking on the project.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run mypy on the project."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Running mypy type checking...")
    result = subprocess.run(
        ["mypy", str(src_dir)],
        capture_output=True,
        text=True,
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 