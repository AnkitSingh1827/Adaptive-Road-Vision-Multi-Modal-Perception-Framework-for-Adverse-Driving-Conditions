import json
from pathlib import Path

def patch_notebook(nb_file: Path):
    if not nb_file.exists():
        return
    with open(nb_file, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    modified = False
    for cell in nb.get('cells', []):
        src = "".join(cell.get('source', []))
        if 'preprocessing_summary.json' in src:
            new_source = []
            for line in cell['source']:
                if '"synthetic_fog_train_only":' in line:
                    new_source.append('        "synthetic_fog_train_only": bool(synthetic_df.empty or synthetic_df["split"].eq("train").all()),\n')
                    modified = True
                elif '"exact_15000_records":' in line:
                    new_source.append('        "exact_15000_records": bool(len(df) == EXPECTED_TOTAL),\n')
                    modified = True
                elif '"exact_70_20_10_split":' in line:
                    new_source.append('        "exact_70_20_10_split": bool(actual_splits == EXPECTED_SPLITS),\n')
                    modified = True
                elif '"all_images_and_labels_exist":' in line:
                    new_source.append('        "all_images_and_labels_exist": bool(not len(missing_images) and not len(missing_labels)),\n')
                    modified = True
                elif '"valid_yolo_labels":' in line:
                    new_source.append('        "valid_yolo_labels": bool(len(label_issues) == 0),\n')
                    modified = True
                elif 'summary_path.write_text(json.dumps(summary, indent=2)' in line:
                    new_source.append('summary_path.write_text(json.dumps(summary, indent=2, default=lambda o: bool(o) if isinstance(o, (np.bool_, np.bool)) else str(o)), encoding="utf-8")\n')
                    modified = True
                elif 'print(json.dumps(summary["checks"], indent=2))' in line:
                    new_source.append('print(json.dumps(summary["checks"], indent=2, default=lambda o: bool(o) if isinstance(o, (np.bool_, np.bool)) else str(o)))\n')
                    modified = True
                else:
                    new_source.append(line)
            cell['source'] = new_source

    if modified:
        with open(nb_file, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Successfully patched {nb_file}")
    return nb

if __name__ == "__main__":
    nb_orig = Path('notebooks/11_preprocessing_FINAL_15K.ipynb')
    nb_data = patch_notebook(nb_orig)
    
    # Also save to 11_data_preprocessing.ipynb
    nb_target = Path('notebooks/11_data_preprocessing.ipynb')
    if nb_data:
        with open(nb_target, 'w', encoding='utf-8') as f:
            json.dump(nb_data, f, indent=1)
        print(f"Synchronized copy to {nb_target}")
