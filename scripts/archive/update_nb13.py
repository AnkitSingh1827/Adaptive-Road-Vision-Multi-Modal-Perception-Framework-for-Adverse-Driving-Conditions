import json
from pathlib import Path

p = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision\notebooks\13_condition_analysis_evaluation.ipynb")
with open(p, "r", encoding="utf-8") as f:
    nb = json.load(f)

c3_source = [
    "required = {\n",
    "    \"Final metadata\": FINAL_METADATA_CSV,\n",
    "    \"Best condition model\": MODEL_PATH,\n",
    "}\n",
    "\n",
    "for name, path in required.items():\n",
    "    status_str = 'OK' if path.exists() else 'MISSING'\n",
    "    print(f\"{name}: {status_str} -> {path}\")\n",
    "\n",
    "missing = [f\"{name}: {path}\" for name, path in required.items() if not path.exists()]\n",
    "\n",
    "if missing:\n",
    "    if not MODEL_PATH.exists() and FINAL_METADATA_CSV.exists():\n",
    "        print(f\"WARNING: Required condition model checkpoint missing: {MODEL_PATH}\\nRun Notebook 12 to train the model. A placeholder model will be used if continuing test run.\")\n",
    "    else:\n",
    "        raise FileNotFoundError(\n",
    "            \"Required Notebook 12 outputs are missing:\\n\" +\n",
    "            \"\\n\".join(missing)\n",
    "        )\n",
    "\n",
    "metadata = pd.read_csv(FINAL_METADATA_CSV)\n",
    "\n",
    "print(\"Metadata shape:\", metadata.shape)\n"
]

nb["cells"][3]["source"] = c3_source
with open(p, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Updated NB13 Cell 3 successfully!")
