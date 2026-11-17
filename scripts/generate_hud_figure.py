import os
import cv2
import matplotlib.pyplot as plt

out_dir = os.path.join("outputs", "paper_figures")
vis_dir = os.path.join("results", "pipeline", "visualizations")

# Select representative adverse driving frames from test pipeline
sample_files = [
    "00000_cabc30fc-e7726578.jpg",
    "00002_cabc30fc-fd79926f.jpg",
    "00010_cabddb96-ca0ac856.jpg",
    "00014_cabf7be1-36a39a28.jpg"
]

images = []
for f in sample_files:
    p = os.path.join(vis_dir, f)
    if os.path.exists(p):
        img = cv2.imread(p)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        images.append((f, img))

if len(images) >= 4:
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.2), dpi=300)
    titles = [
        "(a) Night Driving: Headlight Glare & Pedestrian Tracking",
        "(b) Dense Urban Traffic: Multi-Actor Bounding & Proximity",
        "(c) Wet Highway: Distance Contact-Patch Estimation",
        "(d) Adverse Illumination: ADAS Risk Alert Overlay"
    ]
    for idx, ax in enumerate(axes.flat):
        ax.imshow(images[idx][1])
        ax.set_title(titles[idx], fontsize=9.5, fontweight='bold', pad=4)
        ax.axis('off')
    
    plt.tight_layout()
    fig6_path = os.path.join(out_dir, "fig6_qualitative_hud.png")
    plt.savefig(fig6_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {fig6_path}")
else:
    print(f"Found {len(images)} images.")
