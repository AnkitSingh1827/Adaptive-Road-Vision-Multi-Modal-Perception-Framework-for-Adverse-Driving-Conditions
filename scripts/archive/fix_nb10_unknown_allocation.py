import json
from pathlib import Path

def update_notebook():
    nb_path = Path("notebooks/10_dataset_balance_rebuild_RECOMMENDED.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # 1. Cell 16: take = min(capacities["Unknown"], left)
    cell16 = nb["cells"][16]
    c16_lines = []
    for line in cell16["source"]:
        if 'capacities["Unknown"]' in line and 'round(' in line:
            indent = line[:line.index('take')]
            c16_lines.append(f'{indent}take = min(capacities["Unknown"], left)\n')
        else:
            c16_lines.append(line)
    cell16["source"] = c16_lines

    # 2. Cell 20: copy_or_link_image safe & fast
    cell20 = nb["cells"][20]
    c20_src = "".join(cell20["source"])
    old_copy_func = """def copy_or_link_image(src, dst):
    \"\"\"Copy to an independent file; do not hard-link source data into the new dataset.\"\"\"
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(f"Refusing to overwrite image: {dst}")
    shutil.copy2(src, dst)"""

    new_copy_func = """def copy_or_link_image(src, dst):
    \"\"\"Copy or hardlink image to new dataset; avoid redundant recopying.\"\"\"
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)"""

    if old_copy_func in c20_src:
        c20_src = c20_src.replace(old_copy_func, new_copy_func)
        cell20["source"] = [l + "\n" for l in c20_src.splitlines()]

    # 3. Cell 22: sync final_meta from disk if present
    cell22 = nb["cells"][22]
    c22_lines = cell22["source"]
    first_line = c22_lines[0] if c22_lines else ""
    if "final_dataset_metadata.csv" not in "".join(c22_lines[:5]):
        sync_header = [
            "meta_csv = OUTPUT_ROOT / \"metadata\" / \"final_dataset_metadata.csv\"\n",
            "if meta_csv.exists():\n",
            "    final_meta = pd.read_csv(meta_csv)\n",
            "\n"
        ]
        cell22["source"] = sync_header + c22_lines

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print(f"Successfully updated {nb_path}")

if __name__ == "__main__":
    update_notebook()
