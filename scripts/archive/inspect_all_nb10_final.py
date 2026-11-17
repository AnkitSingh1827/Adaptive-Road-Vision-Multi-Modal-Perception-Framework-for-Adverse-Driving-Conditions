import json

with open("notebooks/10_final_dataset_creation.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for i, cell in enumerate(nb["cells"]):
    print(f"=== Cell {i} ({cell['cell_type']}) ===")
    src = "".join(cell.get("source", []))
    print(src)
