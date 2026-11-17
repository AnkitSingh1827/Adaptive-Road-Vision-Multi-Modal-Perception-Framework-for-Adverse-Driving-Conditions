import os
import matplotlib.pyplot as plt
import numpy as np

# Output directory for paper figures
out_dir = os.path.join("outputs", "paper_figures")
os.makedirs(out_dir, exist_ok=True)

# Set IEEE Publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13
})

# ==============================================================================
# FIGURE 2: Dataset Imbalance vs. Balanced Dataset
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.6), dpi=300)

# (a) Original BDD100K Weather Distribution
conditions = ['Day (Clear)', 'Night', 'Rain', 'Fog']
orig_shares = [52.0, 38.0, 9.2, 0.8]
colors = ['#3498db', '#34495e', '#2ecc71', '#e74c3c']

ax1.bar(conditions, orig_shares, color=colors, edgecolor='black', linewidth=0.8, alpha=0.85)
ax1.set_ylabel('Percentage Share (%)')
ax1.set_title('(a) Original BDD100K Distribution\n(Extreme Fog Scarcity: <0.8%)', fontsize=10, fontweight='bold')
ax1.set_ylim(0, 60)
for i, v in enumerate(orig_shares):
    ax1.text(i, v + 1.2, f"{v}%", ha='center', fontsize=9, fontweight='bold')
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# (b) Balanced 15,000 Dataset with CycleGAN
train_counts = [2518, 2518, 2518, 2932]
val_counts   = [494,  494,  494,  13]
test_counts  = [986,  985,  985,  38]

x = np.arange(len(conditions))
width = 0.25

ax2.bar(x - width, train_counts, width, label='Train (10.5K)', color='#2980b9', edgecolor='black', linewidth=0.7)
ax2.bar(x, val_counts, width, label='Val (1.5K)', color='#f39c12', edgecolor='black', linewidth=0.7)
ax2.bar(x + width, test_counts, width, label='Test (3.0K)', color='#27ae60', edgecolor='black', linewidth=0.7)

ax2.set_xticks(x)
ax2.set_xticklabels(conditions)
ax2.set_ylabel('Number of Images')
ax2.set_title('(b) Balanced Corpus (final_condition_balanced_v2)\n(Synthesized 2,802 Fog Scenes via CycleGAN)', fontsize=10, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
fig_path2 = os.path.join(out_dir, "fig2_dataset_balancing.png")
plt.savefig(fig_path2, dpi=300)
plt.close()
print(f"Generated: {fig_path2}")

# ==============================================================================
# FIGURE 4: False Positive Reduction & Precision Improvement
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.6), dpi=300)

conds = ['Night', 'Rain', 'Fog', 'Overall Total']
raw_fp = [7582, 5436, 135, 21444]
enh_fp = [1895, 1642, 55, 11883]

x = np.arange(len(conds))
width = 0.35

# (a) False Positive Drop
ax1.bar(x - width/2, raw_fp, width, label='Raw Frames', color='#e74c3c', edgecolor='black', linewidth=0.7, alpha=0.85)
ax1.bar(x + width/2, enh_fp, width, label='Enhanced Frames', color='#2ecc71', edgecolor='black', linewidth=0.7, alpha=0.85)
ax1.set_xticks(x)
ax1.set_xticklabels(conds, fontsize=9)
ax1.set_ylabel('False Positive Alarms (Count)')
ax1.set_title('(a) False Positive Alarm Suppression\n(44.6% Overall Reduction: -9,561 Alarms)', fontsize=10, fontweight='bold')
ax1.legend()
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Add reduction annotations
reductions = ["-75.0%", "-69.8%", "-59.3%", "-44.6%"]
for i in range(len(conds)):
    ax1.text(i + width/2, enh_fp[i] + (500 if i==3 else 150), reductions[i], ha='center', fontsize=8, fontweight='bold', color='#27ae60')

# (b) Precision Gains
raw_prec = [63.33, 65.89, 67.93, 64.58]
enh_prec = [76.77, 78.34, 73.93, 69.89]

ax2.bar(x - width/2, raw_prec, width, label='Raw Frames', color='#e67e22', edgecolor='black', linewidth=0.7, alpha=0.85)
ax2.bar(x + width/2, enh_prec, width, label='Enhanced Frames', color='#3498db', edgecolor='black', linewidth=0.7, alpha=0.85)
ax2.set_xticks(x)
ax2.set_xticklabels(conds, fontsize=9)
ax2.set_ylabel('Detection Precision (%)')
ax2.set_ylim(50, 90)
ax2.set_title('(b) Detection Precision Elevation\n(Eliminates Hallucinated Wet-Road Objects)', fontsize=10, fontweight='bold')
ax2.legend(loc='lower right')
ax2.grid(axis='y', linestyle='--', alpha=0.5)

deltas = ["+13.4%", "+12.5%", "+6.0%", "+5.3%"]
for i in range(len(conds)):
    ax2.text(i + width/2, enh_prec[i] + 0.8, deltas[i], ha='center', fontsize=8, fontweight='bold', color='#2980b9')

plt.tight_layout()
fig_path4 = os.path.join(out_dir, "fig4_false_positive_reduction.png")
plt.savefig(fig_path4, dpi=300)
plt.close()
print(f"Generated: {fig_path4}")

# ==============================================================================
# FIGURE 5: Per-Class AP50 Gains for Vulnerable Road Users
# ==============================================================================
fig, ax = plt.subplots(figsize=(8, 3.8), dpi=300)

classes = ['Person', 'Rider', 'Car', 'Truck', 'Bus', 'Motorcycle', 'Bicycle', 'Traffic Light', 'Traffic Sign']
n_ap50 = [43.22, 22.88, 63.29, 43.29, 35.65, 19.54, 19.90, 45.29, 45.78]
s_ap50 = [52.17, 34.16, 69.35, 51.08, 44.69, 35.31, 33.39, 56.04, 57.17]

x = np.arange(len(classes))
width = 0.35

ax.bar(x - width/2, n_ap50, width, label='YOLO11n (2.6M params)', color='#bdc3c7', edgecolor='black', linewidth=0.7)
ax.bar(x + width/2, s_ap50, width, label='YOLO11s (9.4M params - Selected)', color='#2980b9', edgecolor='black', linewidth=0.7)

ax.set_xticks(x)
ax.set_xticklabels(classes, rotation=25, ha='right', fontsize=9)
ax.set_ylabel('Average Precision (AP@50, %)')
ax.set_title('Per-Class AP@50 Comparison: YOLO11n vs. YOLO11s on 3,000 Test Scenes\n(Significant Improvements on Vulnerable Pedestrians and Cyclists)', fontsize=10, fontweight='bold')
ax.set_ylim(0, 80)
ax.legend(loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.5)

for i in range(len(classes)):
    delta = s_ap50[i] - n_ap50[i]
    ax.text(i + width/2, s_ap50[i] + 1.2, f"+{delta:.1f}%", ha='center', fontsize=7.5, fontweight='bold', color='#1a5276')

plt.tight_layout()
fig_path5 = os.path.join(out_dir, "fig5_per_class_map.png")
plt.savefig(fig_path5, dpi=300)
plt.close()
print(f"Generated: {fig_path5}")
