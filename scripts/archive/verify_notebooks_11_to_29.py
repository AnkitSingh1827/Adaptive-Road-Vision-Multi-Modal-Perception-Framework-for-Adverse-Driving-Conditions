import json
import glob
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")

def verify_all_notebooks():
    nb_files = sorted(glob.glob(str(PROJECT_ROOT / "notebooks" / "[12][0-9]_*.ipynb")))
    total_cells = 0
    total_errors = 0
    
    print(f"Found {len(nb_files)} notebooks to verify (11 to 29):")
    for nb_path in nb_files:
        nb_name = Path(nb_path).name
        # Skip 10 if present since we focus on 11-29
        if nb_name.startswith("10_"):
            continue
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
            
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        nb_errors = 0
        for idx, cell in enumerate(code_cells):
            total_cells += 1
            code = "".join(cell["source"])
            # Remove jupyter magic commands for compilation test
            clean_code = "\n".join([line for line in code.split("\n") if not line.strip().startswith("%") and not line.strip().startswith("!")])
            try:
                compile(clean_code, f"{nb_name}_cell_{idx}", "exec")
            except SyntaxError as e:
                print(f"  [ERROR] {nb_name} code cell {idx}: {e}")
                nb_errors += 1
                total_errors += 1
        
        status = "PASSED" if nb_errors == 0 else f"FAILED ({nb_errors} errors)"
        print(f"  {nb_name:45s}: {len(code_cells)} code cells -> {status}")
        
    print(f"\nTotal code cells checked: {total_cells}")
    print(f"Total syntax/compilation errors: {total_errors}")
    assert total_errors == 0, f"Found {total_errors} errors!"
    print("ALL NOTEBOOK CELLS COMPILE CLEANLY WITH 0 ERRORS!")

if __name__ == "__main__":
    verify_all_notebooks()
