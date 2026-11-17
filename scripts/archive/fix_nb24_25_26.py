import json
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")

# Fix NB24
nb24_path = PROJECT_ROOT / "notebooks" / "24_original_vs_enhanced_detection.ipynb"
with open(nb24_path, "r", encoding="utf-8") as f:
    nb24 = json.load(f)

c3_source_24 = [
    "if not SELECTED_PATH.exists():\n",
    "    print(f\"WARNING: Missing {SELECTED_PATH}. Using default detector configuration.\")\n",
    "    selected_detector = \"Detector 1 (Default)\"\n",
    "    selected_model = \"YOLO11n\"\n",
    "    selected_checkpoint = PROJECT_ROOT / \"models\" / \"detection\" / \"final_selected_detector.pt\"\n",
    "    if not selected_checkpoint.exists():\n",
    "        selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "else:\n",
    "    selection = json.loads(SELECTED_PATH.read_text(encoding=\"utf-8\"))\n",
    "    selected_detector = selection[\"selected_detector\"]\n",
    "    selected_model = selection[\"selected_model\"]\n",
    "    selected_checkpoint = Path(selection[\"stable_downstream_checkpoint\"])\n",
    "\n",
    "if selected_checkpoint.name != \"yolo11n.pt\" and not selected_checkpoint.exists():\n",
    "    print(f\"WARNING: Selected checkpoint not found: {selected_checkpoint}. Using pretrained yolo11n.pt for demonstration/test.\")\n",
    "    selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "\n",
    "print(\"Selected detector:\", selected_detector)\n",
    "print(\"Model:\", selected_model)\n",
    "print(\"Checkpoint:\", selected_checkpoint)\n",
    "\n",
    "if not METADATA_PATH.exists():\n",
    "    raise FileNotFoundError(f\"Missing BDD metadata: {METADATA_PATH}\")\n",
    "\n",
    "metadata = pd.read_csv(METADATA_PATH)\n",
    "if \"project_condition\" not in metadata.columns and \"condition\" in metadata.columns:\n",
    "    metadata[\"project_condition\"] = metadata[\"condition\"]\n",
    "test_meta = metadata[metadata[\"split\"].astype(str).str.lower() == \"test\"].copy()\n",
    "\n",
    "print(\"Test metadata rows:\", len(test_meta))\n",
    "print(test_meta[\"project_condition\"].value_counts(dropna=False))\n"
]
nb24["cells"][3]["source"] = c3_source_24
with open(nb24_path, "w", encoding="utf-8") as f:
    json.dump(nb24, f, indent=1)
print("Updated NB24 Cell 3")

# Fix NB25
nb25_path = PROJECT_ROOT / "notebooks" / "25_bytetrack_evaluation.ipynb"
with open(nb25_path, "r", encoding="utf-8") as f:
    nb25 = json.load(f)

c3_source_25 = [
    "if not SELECTION_PATH.exists():\n",
    "    print(f\"WARNING: Missing {SELECTION_PATH}. Using fallback YOLO11n detector.\")\n",
    "    selected_detector = \"Detector 1 (Default)\"\n",
    "    selected_model = \"YOLO11n\"\n",
    "    selected_checkpoint = PROJECT_ROOT / \"models\" / \"detection\" / \"final_selected_detector.pt\"\n",
    "    if not selected_checkpoint.exists():\n",
    "        selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "else:\n",
    "    selection = json.loads(SELECTION_PATH.read_text(encoding=\"utf-8\"))\n",
    "    selected_detector = selection[\"selected_detector\"]\n",
    "    selected_model = selection[\"selected_model\"]\n",
    "    selected_checkpoint = Path(selection[\"stable_downstream_checkpoint\"])\n",
    "    if selected_checkpoint.name != \"yolo11n.pt\" and not selected_checkpoint.exists():\n",
    "        print(f\"WARNING: Selected checkpoint not found: {selected_checkpoint}. Using yolo11n.pt fallback.\")\n",
    "        selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "\n",
    "print(\"Selected detector:\", selected_detector)\n",
    "print(\"Selected model:\", selected_model)\n",
    "print(\"Checkpoint:\", selected_checkpoint)\n",
    "\n",
    "if not METADATA_PATH.exists():\n",
    "    raise FileNotFoundError(f\"Missing metadata: {METADATA_PATH}\")\n",
    "\n",
    "metadata = pd.read_csv(METADATA_PATH)\n",
    "if \"project_condition\" not in metadata.columns and \"condition\" in metadata.columns:\n",
    "    metadata[\"project_condition\"] = metadata[\"condition\"]\n",
    "test_meta = metadata[\n",
    "    metadata[\"split\"].astype(str).str.lower() == \"test\"\n",
    "].copy()\n",
    "\n",
    "print(\"Test rows:\", len(test_meta))\n"
]
nb25["cells"][3]["source"] = c3_source_25
with open(nb25_path, "w", encoding="utf-8") as f:
    json.dump(nb25, f, indent=1)
print("Updated NB25 Cell 3")

# Fix NB26
nb26_path = PROJECT_ROOT / "notebooks" / "26_depth_estimation.ipynb"
with open(nb26_path, "r", encoding="utf-8") as f:
    nb26 = json.load(f)

c4_source_26 = [
    "if not SELECTION_PATH.exists():\n",
    "    print(f\"WARNING: Missing {SELECTION_PATH}. Using fallback YOLO11n detector.\")\n",
    "    selected_detector = \"Detector 1 (Default)\"\n",
    "    selected_model = \"YOLO11n\"\n",
    "    selected_checkpoint = PROJECT_ROOT / \"models\" / \"detection\" / \"final_selected_detector.pt\"\n",
    "    if not selected_checkpoint.exists():\n",
    "        selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "else:\n",
    "    selection = json.loads(SELECTION_PATH.read_text(encoding=\"utf-8\"))\n",
    "    selected_checkpoint = Path(selection[\"stable_downstream_checkpoint\"])\n",
    "    selected_detector = selection[\"selected_detector\"]\n",
    "    selected_model = selection[\"selected_model\"]\n",
    "    if selected_checkpoint.name != \"yolo11n.pt\" and not selected_checkpoint.exists():\n",
    "        print(f\"WARNING: Checkpoint {selected_checkpoint} not found. Using yolo11n.pt fallback.\")\n",
    "        selected_checkpoint = Path(\"yolo11n.pt\")\n",
    "\n",
    "print(\"Selected detector:\", selected_detector)\n",
    "print(\"Selected model:\", selected_model)\n",
    "print(\"Checkpoint:\", selected_checkpoint)\n",
    "\n",
    "metadata = pd.read_csv(METADATA_PATH)\n",
    "if \"project_condition\" not in metadata.columns and \"condition\" in metadata.columns:\n",
    "    metadata[\"project_condition\"] = metadata[\"condition\"]\n",
    "test_meta = metadata[\n",
    "    metadata[\"split\"].astype(str).str.lower() == \"test\"\n",
    "].copy()\n",
    "\n",
    "print(\"Test images in metadata:\", len(test_meta))\n"
]
nb26["cells"][4]["source"] = c4_source_26
with open(nb26_path, "w", encoding="utf-8") as f:
    json.dump(nb26, f, indent=1)
print("Updated NB26 Cell 4")
