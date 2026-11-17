import json
from pathlib import Path

nb_path = Path("notebooks/10_final_dataset_creation.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cell 1: Add link_or_copy helper
cell1_src = "".join(nb["cells"][1]["source"])
if "def link_or_copy" not in cell1_src:
    helper_code = "\nimport os\n\ndef link_or_copy(src, dst):\n    if not dst.exists():\n        try:\n            os.link(src, dst)\n        except Exception:\n            shutil.copy2(src, dst)\n"
    cell1_src += helper_code
    nb["cells"][1]["source"] = [line + "\n" for line in cell1_src.splitlines()]

# Cell 12: Use link_or_copy
cell12_src = "".join(nb["cells"][12]["source"])
cell12_src = cell12_src.replace("shutil.copy2(source_img, destination)", "link_or_copy(source_img, destination)")
cell12_src = cell12_src.replace("shutil.copy2(source_label, FINAL_LABEL / split / label_name)", "link_or_copy(source_label, FINAL_LABEL / split / label_name)")
if "Processed {i+1}" not in cell12_src:
    cell12_src = cell12_src.replace("destination = FINAL_IMG", "if (i + 1) % 25000 == 0:\n        print(f\"Processed {i+1}/100000 records...\")\n    destination = FINAL_IMG")
nb["cells"][12]["source"] = [line + "\n" for line in cell12_src.splitlines()]

# Cell 18: Use link_or_copy
cell18_src = "".join(nb["cells"][18]["source"])
cell18_src = cell18_src.replace("shutil.copy2(source_path, destination)", "link_or_copy(source_path, destination)")
nb["cells"][18]["source"] = [line + "\n" for line in cell18_src.splitlines()]

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 10 optimization applied successfully.")
