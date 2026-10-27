# Test runner script for CI and local verification
import os
import sys
import pytest

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    print("=== RUNNING PAPER RADAR TESTS ===")
    print(f"Python: {sys.version}")
    print(f"Pytest: {pytest.__version__}")
    code = pytest.main(["-v", "tests"])
    print(f"=== PYTEST FINISHED WITH CODE: {code} ===")
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                if code == 0:
                    f.write("### :white_check_mark: All Tests Passed Successfully!")
                else:
                    f.write(f"### :x: Pytest Failed with Code {code}")
        except Exception: pass
    sys.exit(code)
