import json
from pathlib import Path

def update_nb22():
    nb_path = Path("notebooks/22_original_vs_enhanced_detection_CORRECTED.ipynb")
    assert nb_path.exists(), f"Notebook not found: {nb_path}"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    target_idx = None
    for idx, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if "class EnhancementNet" in src or "load_checkpoint_model" in src:
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError("Target cell with EnhancementNet not found in notebook!")

    print(f"Updating cell {target_idx} in {nb_path.name}...")

    new_source_lines = [
        "import torch.nn.functional as F\n",
        "\n",
        "class ResidualBlock(nn.Module):\n",
        "    def __init__(self, channels):\n",
        "        super().__init__()\n",
        "        self.block = nn.Sequential(\n",
        "            nn.Conv2d(channels, channels, 3, padding=1),\n",
        "            nn.InstanceNorm2d(channels, affine=True),\n",
        "            nn.ReLU(inplace=True),\n",
        "            nn.Conv2d(channels, channels, 3, padding=1),\n",
        "            nn.InstanceNorm2d(channels, affine=True),\n",
        "        )\n",
        "\n",
        "    def forward(self, x):\n",
        "        return x + self.block(x)\n",
        "\n",
        "\n",
        "class ConditionEnhancer(nn.Module):\n",
        "    \"\"\"\n",
        "    Compact residual encoder-decoder matching the architecture\n",
        "    trained in Notebooks 14 (Night), 15 (Rain), and 16 (Fog).\n",
        "    \"\"\"\n",
        "    def __init__(self, base_channels=32, num_res_blocks=4):\n",
        "        super().__init__()\n",
        "        self.enc1 = nn.Sequential(\n",
        "            nn.Conv2d(3, base_channels, 3, padding=1),\n",
        "            nn.ReLU(inplace=True),\n",
        "        )\n",
        "        self.enc2 = nn.Sequential(\n",
        "            nn.Conv2d(base_channels, base_channels * 2, 3, stride=2, padding=1),\n",
        "            nn.ReLU(inplace=True),\n",
        "        )\n",
        "        self.enc3 = nn.Sequential(\n",
        "            nn.Conv2d(base_channels * 2, base_channels * 4, 3, stride=2, padding=1),\n",
        "            nn.ReLU(inplace=True),\n",
        "        )\n",
        "        self.res = nn.Sequential(*[ResidualBlock(base_channels * 4) for _ in range(num_res_blocks)])\n",
        "        self.dec2 = nn.Sequential(\n",
        "            nn.Conv2d(base_channels * 4, base_channels * 2, 3, padding=1),\n",
        "            nn.ReLU(inplace=True),\n",
        "        )\n",
        "        self.dec1 = nn.Sequential(\n",
        "            nn.Conv2d(base_channels * 2, base_channels, 3, padding=1),\n",
        "            nn.ReLU(inplace=True),\n",
        "        )\n",
        "        self.out = nn.Conv2d(base_channels, 3, 3, padding=1)\n",
        "\n",
        "    def forward(self, x):\n",
        "        e1 = self.enc1(x)\n",
        "        e2 = self.enc2(e1)\n",
        "        e3 = self.enc3(e2)\n",
        "\n",
        "        z = self.res(e3)\n",
        "\n",
        "        z = F.interpolate(z, size=e2.shape[-2:], mode=\"bilinear\", align_corners=False)\n",
        "        z = self.dec2(z) + e2\n",
        "\n",
        "        z = F.interpolate(z, size=e1.shape[-2:], mode=\"bilinear\", align_corners=False)\n",
        "        z = self.dec1(z) + e1\n",
        "\n",
        "        residual = torch.tanh(self.out(z)) * 0.5\n",
        "        return torch.clamp(x + residual, 0.0, 1.0)\n",
        "\n",
        "\n",
        "# Backward compatibility alias\n",
        "EnhancementNet = ConditionEnhancer\n",
        "\n",
        "\n",
        "def load_checkpoint_model(path):\n",
        "    ckpt = torch.load(path, map_location=TORCH_DEVICE)\n",
        "\n",
        "    if isinstance(ckpt, dict) and \"model_state_dict\" in ckpt:\n",
        "        state = ckpt[\"model_state_dict\"]\n",
        "    elif isinstance(ckpt, dict) and \"state_dict\" in ckpt:\n",
        "        state = ckpt[\"state_dict\"]\n",
        "    elif isinstance(ckpt, dict):\n",
        "        state = ckpt\n",
        "    else:\n",
        "        state = ckpt.state_dict()\n",
        "\n",
        "    cleaned = {}\n",
        "    for k, v in state.items():\n",
        "        cleaned[k.replace(\"module.\", \"\")] = v\n",
        "\n",
        "    model = ConditionEnhancer().to(TORCH_DEVICE)\n",
        "    model.load_state_dict(cleaned, strict=True)\n",
        "    model.eval()\n",
        "    return model\n",
        "\n",
        "\n",
        "enhancer_paths = {\n",
        "    \"Night\": MODEL_ROOT / \"enhancement\" / \"night\" / \"night_enhancer_best.pth\",\n",
        "    \"Rain\": MODEL_ROOT / \"enhancement\" / \"rain\" / \"rain_enhancer_best.pth\",\n",
        "    \"Fog\": MODEL_ROOT / \"enhancement\" / \"fog\" / \"fog_enhancer_best.pth\",\n",
        "}\n",
        "\n",
        "enhancers = {}\n",
        "\n",
        "for condition, path in enhancer_paths.items():\n",
        "    if path.exists():\n",
        "        try:\n",
        "            enhancers[condition] = load_checkpoint_model(path)\n",
        "            print(f\"Loaded {condition}: {path}\")\n",
        "        except Exception as e:\n",
        "            print(f\"Could not load {condition} enhancer: {e}\")\n",
        "    else:\n",
        "        print(f\"Missing {condition} enhancer: {path}\")\n",
        "\n",
        "print(\"Loaded enhancement models:\", list(enhancers.keys()))\n",
        "required_enhancers = set(test_meta[\"project_condition\"].unique()) & {\"Night\", \"Rain\", \"Fog\"}\n",
        "missing_enhancers = sorted(required_enhancers - set(enhancers))\n",
        "if missing_enhancers:\n",
        "    missing_paths = [str(enhancer_paths[c]) for c in missing_enhancers]\n",
        "    raise FileNotFoundError(\n",
        "        \"Required enhancement checkpoint(s) missing or incompatible for test conditions \"\n",
        "        f\"{missing_enhancers}. Expected files: {missing_paths}. Train the relevant Notebook 14/15/16 first.\"\n",
        "    )\n",
    ]

    nb["cells"][target_idx]["source"] = new_source_lines
    # Clear old execution outputs from error
    nb["cells"][target_idx]["outputs"] = []
    nb["cells"][target_idx]["execution_count"] = None

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"Successfully updated cell {target_idx} in {nb_path.name}!")

if __name__ == "__main__":
    update_nb22()
