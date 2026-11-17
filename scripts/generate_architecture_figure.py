import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Output directory
out_dir = os.path.join("outputs", "paper_figures")
os.makedirs(out_dir, exist_ok=True)

fig = plt.figure(figsize=(14, 8.8), dpi=300)
ax = fig.add_subplot(111)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color palette - professional academic IEEE theme
c_input = '#1f2d3d'
c_classifier = '#1b4f72'
c_router = '#117864'
c_enhancer = '#5b2c6f'
c_bypass = '#196f3d'
c_restored = '#212f3d'
c_detector = '#935116'
c_depth = '#1f618d'
c_tracker = '#b9770e'
c_risk = '#922b21'
c_hud = '#145a32'

def draw_box(ax, x, y, w, h, title, subtitle="", color='#2c3e50', bg='#ffffff', lw=2.0, fontsize=10.5, subfontsize=8.5, corner=2):
    rect = patches.FancyBboxPatch((x, y), w, h,
                                  boxstyle=f"round,pad=0.2,rounding_size={corner}",
                                  ec=color, fc=bg, lw=lw, zorder=2)
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w/2, y + h*0.64, title, ha='center', va='center', fontsize=fontsize, fontweight='bold', color=color, zorder=3)
        ax.text(x + w/2, y + h*0.28, subtitle, ha='center', va='center', fontsize=subfontsize, color='#2c3e50', zorder=3)
    else:
        ax.text(x + w/2, y + h*0.5, title, ha='center', va='center', fontsize=fontsize, fontweight='bold', color=color, zorder=3)

def draw_arrow(ax, x1, y1, x2, y2, color='#2c3e50', lw=2.0, text=""):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=16), zorder=1)
    if text:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(mid_x, mid_y + 1.2, text, ha='center', va='bottom', fontsize=8, fontweight='bold', color=color, backgroundcolor='#ffffff', zorder=4)

# -------------------------------------------------------------
# 1. INPUT LAYER
# -------------------------------------------------------------
draw_box(ax, 3, 76, 17, 10, "Raw Camera Frame", "RGB Stream (H x W x 3)", color=c_input, bg='#ebedef', lw=2.2, fontsize=10.5)

# -------------------------------------------------------------
# 2. STAGE 1: MULTI-TASK CONDITION CLASSIFIER
# -------------------------------------------------------------
draw_box(ax, 25, 76, 26, 10, "Stage 1: Multi-Task Classifier", "ResNet-18 Backbone (80.07% Accuracy)\nTime: Day/Night | Weather: Clear/Rain/Fog", color=c_classifier, bg='#ebf5fb', lw=2.2, fontsize=10.5)
draw_arrow(ax, 20.2, 81, 24.8, 81, color=c_classifier, lw=2.2)

# -------------------------------------------------------------
# 3. STAGE 2: ADAPTIVE ROUTER (Diamond)
# -------------------------------------------------------------
router_x, router_y = 59, 81
r_w, r_h = 6.5, 6.5
pts = [[router_x, router_y + r_h], [router_x + r_w, router_y], [router_x, router_y - r_h], [router_x - r_w, router_y]]
diamond = patches.Polygon(pts, closed=True, ec=c_router, fc='#e8f8f5', lw=2.2, zorder=2)
ax.add_patch(diamond)
ax.text(router_x, router_y + 0.8, "Stage 2", ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_router, zorder=3)
ax.text(router_x, router_y - 1.2, "Adaptive\nRouter", ha='center', va='center', fontsize=8, fontweight='bold', color=c_router, zorder=3)
draw_arrow(ax, 51.2, 81, 52.3, 81, color=c_router, lw=2.2)

# -------------------------------------------------------------
# 4. ENHANCERS (4 Branches)
# -------------------------------------------------------------
draw_box(ax, 74, 90, 22, 6.5, "Night Enhancer", "Residual U-Net Low-Light Restoration", color=c_enhancer, bg='#f4ecf7', lw=1.8, fontsize=9.5, subfontsize=7.8)
draw_box(ax, 74, 82, 22, 6.5, "Rain Enhancer", "Streak & Specular Reflection Suppression", color=c_enhancer, bg='#f4ecf7', lw=1.8, fontsize=9.5, subfontsize=7.8)
draw_box(ax, 74, 74, 22, 6.5, "Fog Enhancer", "Dark-Channel Dehazing Residual U-Net", color=c_enhancer, bg='#f4ecf7', lw=1.8, fontsize=9.5, subfontsize=7.8)
draw_box(ax, 74, 66, 22, 6.5, "Daylight Bypass", "0 ms Latency | Zero Distortion Pass-Through", color=c_bypass, bg='#eafaf1', lw=2.0, fontsize=9.5, subfontsize=7.8)

# Connectors Router -> Enhancers
ax.plot([65.8, 69.5, 69.5, 73.8], [81, 81, 93.2, 93.2], color=c_enhancer, lw=1.8, zorder=1)
draw_arrow(ax, 69.5, 93.2, 73.8, 93.2, color=c_enhancer, lw=1.8)

ax.plot([65.8, 71, 71, 73.8], [81, 81, 85.2, 85.2], color=c_enhancer, lw=1.8, zorder=1)
draw_arrow(ax, 71, 85.2, 73.8, 85.2, color=c_enhancer, lw=1.8)

ax.plot([65.8, 71, 71, 73.8], [81, 81, 77.2, 77.2], color=c_enhancer, lw=1.8, zorder=1)
draw_arrow(ax, 71, 77.2, 73.8, 77.2, color=c_enhancer, lw=1.8)

ax.plot([65.8, 69.5, 69.5, 73.8], [81, 81, 69.2, 69.2], color=c_bypass, lw=1.8, zorder=1)
draw_arrow(ax, 69.5, 69.2, 73.8, 69.2, color=c_bypass, lw=1.8)

# -------------------------------------------------------------
# 5. RESTORED / ENHANCED FRAME
# -------------------------------------------------------------
draw_box(ax, 34, 52, 32, 8.5, "Enhanced / Restored Frame", "Selective Residual Addition: I_restored = I + R(I)", color=c_restored, bg='#eaeded', lw=2.2, fontsize=10.5, subfontsize=8.5)

# Converging arrows to Restored Frame
ax.plot([96.2, 98, 98, 50, 50], [93.2, 93.2, 62.5, 62.5, 60.7], color=c_enhancer, lw=1.8, zorder=1)
ax.plot([96.2, 98], [85.2, 85.2], color=c_enhancer, lw=1.8, zorder=1)
ax.plot([96.2, 98], [77.2, 77.2], color=c_enhancer, lw=1.8, zorder=1)
ax.plot([96.2, 98], [69.2, 69.2], color=c_bypass, lw=1.8, zorder=1)
draw_arrow(ax, 50, 62, 50, 60.7, color=c_restored, lw=2.2)

# -------------------------------------------------------------
# 6. DUAL BRANCH PERCEPTION (STAGES 3 & 4)
# -------------------------------------------------------------
# Stage 3: Object Detection (Left)
draw_box(ax, 5, 36, 40, 9, "Stage 3: 2D Object Detection", "Fine-Tuned YOLO11s (10 BDD100K Classes, 43.34% mAP@50)\nBounding Boxes [x, y, w, h] & Confidences (>= 0.25)", color=c_detector, bg='#fbeee6', lw=2.2, fontsize=10.5, subfontsize=8)

# Stage 4: Monocular Depth (Right)
draw_box(ax, 55, 36, 40, 9, "Stage 4: Relative Monocular Depth", "Depth Anything V2 Small Foundation Model\nGround-Contact Patch Proximity: Bottom 30% Contact Envelope", color=c_depth, bg='#ebf5fb', lw=2.2, fontsize=10.5, subfontsize=8)

# Branch arrows from Restored Frame
ax.plot([42, 42, 25, 25], [51.8, 48, 48, 45.2], color=c_detector, lw=2.0, zorder=1)
draw_arrow(ax, 25, 47, 25, 45.2, color=c_detector, lw=2.0)

ax.plot([58, 58, 75, 75], [51.8, 48, 48, 45.2], color=c_depth, lw=2.0, zorder=1)
draw_arrow(ax, 75, 47, 75, 45.2, color=c_depth, lw=2.0)

# -------------------------------------------------------------
# 7. STAGE 5: OBJECT TRACKING (BYTETRACK)
# -------------------------------------------------------------
draw_box(ax, 5, 21, 40, 8.5, "Stage 5: Object Tracking (ByteTrack)", "Hierarchical Kalman Association (High/Low Confidence)\nTrajectory Continuity & Persistent Track IDs Across Frames", color=c_tracker, bg='#fef9e7', lw=2.2, fontsize=10.5, subfontsize=8)
draw_arrow(ax, 25, 35.8, 25, 29.7, color=c_tracker, lw=2.2)

# -------------------------------------------------------------
# 8. STAGE 6: MULTI-FACTOR COLLISION RISK ENGINE
# -------------------------------------------------------------
draw_box(ax, 6, 8, 88, 8.8, "Stage 6: Multi-Factor Situational Collision Risk Engine", "Risk = min(1.0,  (Proximity)^1.3  x  Class_Weight  x  Weather_Multiplier  x  Confidence  x  Persistence)\nPedestrians (1.30) | Cyclists (1.25) | Weather Hazards: Fog (1.25x), Night (1.20x), Rain (1.15x)", color=c_risk, bg='#fdedec', lw=2.4, fontsize=11, subfontsize=8.5)

# Arrows feeding into Risk Engine
ax.plot([25, 25, 35, 35], [20.8, 18.5, 18.5, 17.0], color=c_risk, lw=2.0, zorder=1)
draw_arrow(ax, 35, 18.5, 35, 17.0, color=c_risk, lw=2.0, text="Track IDs & Age")

ax.plot([75, 75, 65, 65], [35.8, 18.5, 18.5, 17.0], color=c_risk, lw=2.0, zorder=1)
draw_arrow(ax, 65, 18.5, 65, 17.0, color=c_risk, lw=2.0, text="Proximity Maps")

# -------------------------------------------------------------
# 9. STAGE 7: ADAS TELEMETRY HUD & WARNING TIERS
# -------------------------------------------------------------
draw_box(ax, 3, 0.6, 94, 5.2, "Stage 7: Real-Time ADAS Telemetry HUD & 5-Tier Safety Alert Arbitration (32.4 FPS)", "SAFE [0.0 - 0.25)   |   LOW [0.25 - 0.50)   |   MEDIUM [0.50 - 0.75)   |   HIGH [0.75 - 0.88)   |   CRITICAL [0.88 - 1.00]", color=c_hud, bg='#eafaf1', lw=2.2, fontsize=10, subfontsize=8.5)
draw_arrow(ax, 50, 7.8, 50, 6.0, color=c_hud, lw=2.2)

# Save figure
plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig1_path = os.path.join(out_dir, "fig1_system_architecture.png")
plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Successfully generated Figure 1: {fig1_path}")
