import json
from pathlib import Path

notebooks = [
    '10_balanced_10k_dataset_creation.ipynb',
    '10_class_balanced_10k_dataset_creation.ipynb',
    '10_final_dataset_creation.ipynb'
]

total_errors = 0

for nb_name in notebooks:
    nb_path = Path("notebooks") / nb_name
    print("=" * 70)
    print("VALIDATING:", nb_name)
    print("=" * 70)
    try:
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        print(f"JSON structure: VALID ({len(nb.get('cells', []))} cells)")
    except Exception as e:
        print(f"JSON ERROR: {e}")
        total_errors += 1
        continue

    # Check syntax of each code cell
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    syntax_errors = 0
    for idx, cell in enumerate(code_cells):
        src = "".join(cell.get("source", []))
        lines = []
        for line in src.splitlines():
            if line.strip().startswith("%") or line.strip().startswith("!"):
                lines.append("# " + line)
            else:
                lines.append(line)
        code = "\n".join(lines)
        try:
            compile(code, f"{nb_name}_cell_{idx}", "exec")
        except SyntaxError as e:
            print(f"  Code cell {idx} SyntaxError: {e}")
            syntax_errors += 1

    if syntax_errors == 0:
        print(f"Code syntax: ALL {len(code_cells)} CODE CELLS COMPILE CLEANLY")
    else:
        print(f"Code syntax: {syntax_errors} ERRORS")
        total_errors += syntax_errors

    # Check for CUTM or invalid hardcoded root
    nb_text = json.dumps(nb)
    if "CUTM" in nb_text:
        print("  WARNING: 'CUTM' found in notebook content!")
        total_errors += 1
    else:
        print("  No legacy 'CUTM' paths found.")

print("\n" + "=" * 70)
if total_errors == 0:
    print("ALL NOTEBOOKS VALIDATED SUCCESSFULLY! 0 ERRORS.")
else:
    print(f"VALIDATION FAILED WITH {total_errors} ERRORS.")
print("=" * 70)
