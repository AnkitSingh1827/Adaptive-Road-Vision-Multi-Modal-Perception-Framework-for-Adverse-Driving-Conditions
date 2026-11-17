import json
from pathlib import Path

p = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision\notebooks\27_risk_engine.ipynb")
with open(p, "r", encoding="utf-8") as f:
    nb = json.load(f)

c7_source = [
    "if not DEPTH_PATH.exists() or not TRACK_PATH.exists():\n",
    "    print(\"WARNING: Depth or tracking inputs missing. Run Notebooks 25 & 26 to generate real inputs.\")\n",
    "    print(\"         Using demonstration fallback sample so risk calculation formulas can be verified.\")\n",
    "    depth_df = pd.DataFrame([\n",
    "        {\"image_name\": \"demo_001.jpg\", \"condition\": \"Night\", \"class_id\": 0, \"confidence\": 0.85, \"relative_depth\": 0.35, \"distance_m\": 12.5, \"detection_index\": 0},\n",
    "        {\"image_name\": \"demo_001.jpg\", \"condition\": \"Night\", \"class_id\": 2, \"confidence\": 0.90, \"relative_depth\": 0.20, \"distance_m\": 6.8, \"detection_index\": 1},\n",
    "        {\"image_name\": \"demo_002.jpg\", \"condition\": \"Rain\", \"class_id\": 1, \"confidence\": 0.78, \"relative_depth\": 0.50, \"distance_m\": 18.2, \"detection_index\": 0},\n",
    "    ])\n",
    "    tracking_df = pd.DataFrame([\n",
    "        {\"image_name\": \"demo_001.jpg\", \"sequence_id\": \"seq_01\", \"frame_number\": 1, \"active_tracks\": 2, \"track_ids\": \"1,2\"},\n",
    "        {\"image_name\": \"demo_002.jpg\", \"sequence_id\": \"seq_01\", \"frame_number\": 2, \"active_tracks\": 1, \"track_ids\": \"3\"},\n",
    "    ])\n",
    "else:\n",
    "    depth_df = pd.read_csv(DEPTH_PATH)\n",
    "    tracking_df = pd.read_csv(TRACK_PATH)\n",
    "\n",
    "selection = {}\n",
    "if SELECTION_PATH.exists():\n",
    "    selection = json.loads(\n",
    "        SELECTION_PATH.read_text(encoding=\"utf-8\")\n",
    "    )\n",
    "\n",
    "print(\"Depth rows:\", len(depth_df))\n",
    "print(\"Tracking rows:\", len(tracking_df))\n",
    "print(\n",
    "    \"Selected detector:\",\n",
    "    selection.get(\"selected_detector\", \"not recorded\")\n",
    ")\n",
    "\n",
    "display(depth_df.head())\n",
    "display(tracking_df.head())\n"
]

nb["cells"][7]["source"] = c7_source
with open(p, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Updated NB27 Cell 7 successfully!")
