"""
Adaptive Road Vision Enhancement & Risk-Aware Object Detection
Professional Streamlit Dashboard
"""
from __future__ import annotations
import io, json, sys, time, tempfile
from collections import Counter, deque
from pathlib import Path

import cv2
import imageio
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# ── project root on sys.path ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="Adaptive Road Vision",
    page_icon="\U0001f697",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:linear-gradient(135deg,#0d0f14 0%,#111720 50%,#0a0d12 100%)}
[data-testid="stSidebar"]{background:rgba(15,18,28,.97);border-right:1px solid rgba(99,102,241,.18)}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#c7d2fe}
h1{background:linear-gradient(90deg,#818cf8,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}
h2,h3{color:#e2e8f0;font-weight:700}
[data-testid="metric-container"]{background:rgba(30,35,55,.85);border:1px solid rgba(99,102,241,.25);border-radius:12px;padding:16px 20px;backdrop-filter:blur(12px);transition:box-shadow .2s}
[data-testid="metric-container"]:hover{box-shadow:0 0 18px rgba(129,140,248,.2)}
[data-testid="stMetricLabel"]{color:#94a3b8!important;font-size:.8rem!important}
[data-testid="stMetricValue"]{color:#e2e8f0!important;font-size:1.8rem!important;font-weight:700}
[data-baseweb="tab-list"]{background:rgba(20,25,40,.8);border-radius:10px;border:1px solid rgba(99,102,241,.15)}
[data-baseweb="tab"]{color:#64748b;font-weight:500}
[aria-selected="true"]{color:#818cf8!important;border-bottom:2px solid #818cf8!important}
.stButton>button{background:linear-gradient(135deg,#4f46e5,#6366f1);color:#fff;border:none;border-radius:8px;font-weight:600;transition:transform .15s,box-shadow .15s}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(99,102,241,.4)}
[data-testid="stFileUploader"]{border:2px dashed rgba(99,102,241,.4);border-radius:12px;background:rgba(20,25,40,.6)}
.risk-safe{background:rgba(34,197,94,.12);border-left:4px solid #22c55e;padding:10px 16px;border-radius:6px;color:#86efac}
.risk-low{background:rgba(234,179,8,.10);border-left:4px solid #eab308;padding:10px 16px;border-radius:6px;color:#fde047}
.risk-medium{background:rgba(249,115,22,.12);border-left:4px solid #f97316;padding:10px 16px;border-radius:6px;color:#fdba74}
.risk-high{background:rgba(239,68,68,.14);border-left:4px solid #ef4444;padding:10px 16px;border-radius:6px;color:#fca5a5}
.risk-critical{background:rgba(220,38,38,.20);border-left:4px solid #dc2626;padding:10px 16px;border-radius:6px;color:#f87171;animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.65}}
hr{border:0;border-top:1px solid rgba(99,102,241,.15);margin:1.5rem 0}
.stProgress>div>div{background:linear-gradient(90deg,#4f46e5,#38bdf8)!important;border-radius:4px}
.stCaption{color:#64748b!important}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════
MODELS_DIR  = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RISK_COLORS = {"SAFE":"#22c55e","LOW":"#eab308","MEDIUM":"#f97316","HIGH":"#ef4444","CRITICAL":"#dc2626"}
RISK_CSS    = {"SAFE":"risk-safe","LOW":"risk-low","MEDIUM":"risk-medium","HIGH":"risk-high","CRITICAL":"risk-critical"}
RISK_ICONS  = {"SAFE":"[SAFE]","LOW":"[LOW]","MEDIUM":"[MED]","HIGH":"[HIGH]","CRITICAL":"[!!!]"}
COND_COLORS = {"Day":"#facc15","Night":"#818cf8","Rain":"#38bdf8","Fog":"#94a3b8"}

SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"

def pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO(); img.save(buf, format=fmt); return buf.getvalue()

def colorize_depth_map(depth_map: np.ndarray) -> Image.Image:
    """Converts a float depth map to an inferno colormap RGB Image."""
    if depth_map is None:
        return None
    d_min, d_max = float(depth_map.min()), float(depth_map.max())
    norm = ((depth_map - d_min) / (d_max - d_min + 1e-8) * 255).astype(np.uint8)
    colorized = cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO)
    return Image.fromarray(cv2.cvtColor(colorized, cv2.COLOR_BGR2RGB))

# ══════════════════════════════════════════════════════════════════════════════
# Model inventory
# ══════════════════════════════════════════════════════════════════════════════
def _model_inventory() -> dict:
    inv = {}
    cm = MODELS_DIR / "condition" / "condition_multitask_best.pth"
    cb = MODELS_DIR / "condition" / "condition_resnet18_best.pth"
    inv["condition"]      = cm.is_file() or cb.is_file()
    inv["condition_path"] = str(cm if cm.is_file() else cb) if inv["condition"] else "Not found"
    det_order = [
        MODELS_DIR / "detection" / "final_selected_detector.pt",
        MODELS_DIR / "detection" / "detector_2_best.pt",
        MODELS_DIR / "detection" / "detector_1_best.pt",
    ]
    det = next((p for p in det_order if p.is_file()), None)
    inv["detector"]      = det is not None
    inv["detector_path"] = det.name if det else "Not found"
    for c in ("night", "rain", "fog"):
        inv[f"enhancer_{c}"] = (MODELS_DIR / "enhancement" / c / f"{c}_enhancer_best.pth").is_file()
    return inv

# ══════════════════════════════════════════════════════════════════════════════
# Pipeline (cached)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_pipeline(use_depth: bool = False, use_enhancement: bool = True):
    from src.pipeline.inference import AdaptiveRoadVisionPipeline
    return AdaptiveRoadVisionPipeline(use_enhancement=use_enhancement, use_depth=use_depth)

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:12px 0 4px">
          <div style="font-size:2.5rem">\U0001f697</div>
          <div style="font-size:1.1rem;font-weight:800;background:linear-gradient(90deg,#818cf8,#38bdf8);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent">Adaptive Road Vision</div>
          <div style="font-size:.72rem;color:#475569;margin-top:2px">AI-Powered ADAS Intelligence</div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        st.markdown("#### Model Status")
        inv  = _model_inventory()
        rows = [
            ("Condition Classifier", inv["condition"]),
            ("YOLO Detector",        inv["detector"]),
            ("Night Enhancer",       inv["enhancer_night"]),
            ("Rain Enhancer",        inv["enhancer_rain"]),
            ("Fog Enhancer",         inv["enhancer_fog"]),
        ]
        for name, ok in rows:
            icon  = "OK" if ok else "!!"
            color = "#4ade80" if ok else "#fb923c"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:4px 0;font-size:.82rem"><span style="color:#94a3b8">{name}</span>'
                f'<span style="color:{color};font-weight:700">{icon}</span></div>',
                unsafe_allow_html=True)
        st.divider()

        st.markdown("#### Inference Settings")
        conf_thresh = st.slider("Detection Confidence", 0.10, 0.80, 0.25, 0.05, key="conf_thresh")
        iou_thresh  = st.slider("NMS IoU Threshold",    0.20, 0.80, 0.50, 0.05, key="iou_thresh")
        use_enhance = st.toggle("Adaptive Enhancement", value=True,  key="use_enhance")
        use_depth   = st.toggle("Depth Estimation (slow)", value=False, key="use_depth")
        st.divider()

        with st.expander("Checkpoint Paths", expanded=False):
            st.caption(f"Condition: {inv['condition_path']}")
            st.caption(f"Detector:  {inv['detector_path']}")
        st.divider()
        st.caption("Adaptive Road Vision  |  Deep Learning Project")

    return {"conf_thresh": conf_thresh, "iou_thresh": iou_thresh,
            "use_enhance": use_enhance, "use_depth": use_depth}

# ══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════════════════
def _render_kpis(result: dict, wall_ms: float):
    condition  = result.get("condition", "Day")
    risk_level = result.get("risk_level", "SAFE")
    risk_score = result.get("frame_risk_score", 0.0)
    n_objects  = result.get("detected_objects_count", 0)
    n_critical = result.get("critical_objects_count", 0)
    latency    = result.get("latency_ms", wall_ms)
    fps_val    = result.get("fps", 0.0)
    enhanced   = result.get("was_enhanced", False)
    cond_conf  = result.get("confidence_condition", 1.0)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Condition", condition, delta=f"{cond_conf*100:.0f}% conf")
    with c2: st.metric("Enhanced",  "Yes" if enhanced else "No")
    with c3: st.metric("Objects",   n_objects,
                       delta=f"{n_critical} critical" if n_critical else None,
                       delta_color="inverse" if n_critical else "off")
    with c4: st.metric("Risk Level", risk_level, delta=f"{risk_score:.3f}",
                       delta_color="inverse" if risk_level in ["HIGH","CRITICAL"] else "normal")
    with c5: st.metric("Latency",   f"{latency:.0f} ms", delta=f"{fps_val:.1f} FPS", delta_color="off")


def _render_risk_banner(result: dict):
    risk_level = result.get("risk_level", "SAFE")
    risk_score = result.get("frame_risk_score", 0.0)
    n_objects  = result.get("detected_objects_count", 0)
    n_critical = result.get("critical_objects_count", 0)
    css = RISK_CSS.get(risk_level, "risk-safe")
    lbl = RISK_ICONS.get(risk_level, "")
    st.markdown(
        f'<div class="{css}" style="font-size:.95rem;font-weight:600">'
        f'{lbl} Frame Risk: <strong>{risk_level}</strong>'
        f' &nbsp;|&nbsp; Score: {risk_score:.4f}'
        f' &nbsp;|&nbsp; {n_objects} object(s)'
        f' &nbsp;|&nbsp; {n_critical} critical</div>',
        unsafe_allow_html=True)


def _render_objects_table(objects: list):
    if not objects:
        return
    rows = []
    for obj in objects:
        rs = obj.get("risk_score", 0.0)
        rows.append({
            "Track ID":   obj.get("track_id", "--"),
            "Class":      obj.get("class_name", "--"),
            "Confidence": f'{obj.get("confidence", 0):.3f}',
            "Proximity":  f'{obj.get("proximity", 0):.3f}',
            "Risk Score": f'{rs:.4f}',
            "Critical":   "YES" if obj.get("is_critical") else "No",
        })
    st.dataframe(
        pd.DataFrame(rows), hide_index=True, width="stretch",
        column_config={"Risk Score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=1, format="%.4f")})


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Single Image (Deep Learning Multi-Stage Pipeline)
# ══════════════════════════════════════════════════════════════════════════════
def tab_single_image(cfg: dict):
    st.markdown("### Single Image Analysis & ADAS Deep Learning Pipeline")
    st.caption(
        "Upload a road dashcam image or pick a benchmark preset to inspect all 5 deep learning stages: "
        "Multi-Task Condition Classifier, Adaptive CNN Enhancement, YOLO Object Detection, "
        "Monocular Depth Proximity, and Situational Collision Risk."
    )

    sample_files = sorted(list(SAMPLES_DIR.glob("*.jpg"))) if SAMPLES_DIR.is_dir() else []

    # Preset Quick-Load Scenarios
    if sample_files:
        st.markdown("##### Quick-Load Scenario Presets")
        pr1, pr2, pr3, pr4 = st.columns(4)
        with pr1:
            if st.button("Day Highway", width="stretch", key="preset_day"):
                st.session_state["single_active_img"] = str(sample_files[0])
                st.session_state["single_active_name"] = "Preset: Day Highway"
        with pr2:
            if st.button("Night Urban", width="stretch", key="preset_night"):
                idx = min(2, len(sample_files) - 1)
                st.session_state["single_active_img"] = str(sample_files[idx])
                st.session_state["single_active_name"] = "Preset: Night Urban"
        with pr3:
            if st.button("Rain Wet Road", width="stretch", key="preset_rain"):
                idx = min(4, len(sample_files) - 1)
                st.session_state["single_active_img"] = str(sample_files[idx])
                st.session_state["single_active_name"] = "Preset: Rain Wet Road"
        with pr4:
            if st.button("Foggy / Dense Haze", width="stretch", key="preset_fog"):
                idx = min(6, len(sample_files) - 1)
                st.session_state["single_active_img"] = str(sample_files[idx])
                st.session_state["single_active_name"] = "Preset: Foggy Road"

    uploaded = st.file_uploader(
        "Or Upload Custom Image (JPG / PNG / WebP)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="single_upload"
    )

    if uploaded is not None:
        pil_img = Image.open(uploaded).convert("RGB")
        img_name = uploaded.name
    elif "single_active_img" in st.session_state and Path(st.session_state["single_active_img"]).is_file():
        pil_img = Image.open(st.session_state["single_active_img"]).convert("RGB")
        img_name = st.session_state.get("single_active_name", "Benchmark Sample")
    else:
        st.markdown("""
        <div style="border:2px dashed rgba(99,102,241,.3);border-radius:16px;padding:60px 40px;
             text-align:center;margin-top:20px;background:rgba(15,18,28,.5)">
          <div style="font-size:3.5rem;margin-bottom:12px">\U0001f6e3</div>
          <div style="font-size:1.25rem;font-weight:700;color:#e2e8f0;margin-bottom:8px">
            Select a Scenario Preset Above or Upload a Road Image</div>
          <div style="color:#94a3b8;font-size:.9rem;max-width:540px;margin:0 auto">
            Inspect real-time Condition Classification &rarr; Adaptive Enhancement &rarr;
            YOLO Object Detection &rarr; Depth Proximity &rarr; Collision Risk Telemetry.
          </div>
        </div>""", unsafe_allow_html=True)
        return

    # Real-Time Interactive Fine-Tuning Bar
    st.markdown("---")
    c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns(4)
    with c_ctrl1:
        s_conf = st.slider("Detection Confidence", 0.10, 0.85, cfg["conf_thresh"], 0.05, key="s_conf_sl")
    with c_ctrl2:
        s_iou = st.slider("NMS IoU Threshold", 0.20, 0.80, cfg["iou_thresh"], 0.05, key="s_iou_sl")
    with c_ctrl3:
        s_enhance = st.toggle("Apply Adaptive Restorer", value=cfg["use_enhance"], key="s_enh_tog")
    with c_ctrl4:
        s_depth = st.toggle("Estimate Depth Proximity", value=cfg["use_depth"], key="s_dep_tog")

    # Load Pipeline & Run Inference
    with st.spinner("Executing deep learning perception pipeline..."):
        try:
            pipeline = load_pipeline(use_depth=s_depth, use_enhancement=s_enhance)
        except Exception as exc:
            st.error(f"Failed to load pipeline: {exc}")
            return

        t0 = time.perf_counter()
        try:
            result = pipeline.process_frame(
                pil_img,
                frame_idx=0,
                conf_thresh=s_conf,
                iou_thresh=s_iou,
                return_visualization=True
            )
        except Exception as exc:
            st.error(f"Inference error: {exc}")
            st.exception(exc)
            return
        wall_ms = (time.perf_counter() - t0) * 1000

    # Real-Time KPIs & Alert Banner
    _render_kpis(result, wall_ms)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _render_risk_banner(result)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # 5 Deep Learning Stage Tabs
    stage_tab1, stage_tab2, stage_tab3, stage_tab4, stage_tab5 = st.tabs([
        "ADAS Vision & Risk HUD",
        "Stage 1: Condition Classifier",
        "Stage 2: Adaptive Enhancement",
        "Stage 3 & 4: YOLO & Depth",
        "Stage 5: Collision Risk Matrix",
    ])

    # ── Stage Tab 1: ADAS Vision & Risk HUD ───────────────────────────────────
    with stage_tab1:
        st.markdown("##### Real-Time Perception: Raw Input vs Full ADAS Overlay")
        vis_col1, vis_col2 = st.columns(2)
        vis_img = result.get("visualization", pil_img)
        with vis_col1:
            st.markdown(f"**Raw Camera Input** &nbsp;`{img_name}` ({pil_img.width}x{pil_img.height})")
            st.image(pil_img, width="stretch")
        with vis_col2:
            st.markdown("**Unified ADAS Vision Overlay** (Enhanced + Detection + Risk HUD)")
            st.image(vis_img, width="stretch")
            st.download_button(
                "Download Annotated Image",
                pil_to_bytes(vis_img),
                "adaptive_road_vision_annotated.png",
                mime="image/png",
                width="stretch",
                key="dl_single_vis"
            )

    # ── Stage Tab 2: Condition Classifier ─────────────────────────────────────
    with stage_tab2:
        st.markdown("##### Stage 1 — Multi-Task Condition Classifier (ResNet-18 Backbone)")
        c_info = result.get("condition_info", {})
        cond_name = result.get("condition", "Day")
        cond_conf = result.get("confidence_condition", 1.0)

        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            st.metric("Primary Scene Condition", cond_name, delta=f"{cond_conf * 100:.1f}% Confidence")
        with cs2:
            st.metric("Time of Day Axis", c_info.get("time", "Day" if cond_name != "Night" else "Night"))
        with cs3:
            st.metric("Atmospheric Weather Axis", c_info.get("weather", "Clear" if cond_name not in ["Rain", "Fog"] else cond_name))

        st.markdown("###### Softmax Output Probabilities Across Condition Classes")
        class_probs = c_info.get("class_probabilities", {})
        if class_probs:
            prob_df = pd.DataFrame(list(class_probs.items()), columns=["Condition", "Probability"]).set_index("Condition")
            st.bar_chart(prob_df, color=["#818cf8"])
        else:
            st.info(f"Model classified dominant atmospheric condition as: **{cond_name}** ({cond_conf*100:.1f}%)")

    # ── Stage Tab 3: Adaptive Enhancement ─────────────────────────────────────
    with stage_tab3:
        st.markdown("##### Stage 2 — Adaptive Neural Restorer (Residual U-Net CNN)")
        was_enhanced = result.get("was_enhanced", False)
        enh_img = result.get("enhanced_image")

        if was_enhanced and enh_img is not None:
            st.success(f"Atmospheric condition **{cond_name}** triggered active CNN restoration!")
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown("**Original Degraded Pixels**")
                st.image(pil_img, width="stretch")
            with e_col2:
                st.markdown(f"**Restored Frame** ({cond_name} Enhancer Model)")
                st.image(enh_img, width="stretch")

            # Deep learning restoration delta
            raw_arr = np.array(pil_img).astype(np.float32)
            enh_arr = np.array(enh_img).astype(np.float32)
            lum_gain = (enh_arr.mean() - raw_arr.mean()) / (raw_arr.mean() + 1e-6) * 100
            diff_metric = np.mean(np.abs(enh_arr - raw_arr))

            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Luminance Gain", f"{lum_gain:+.1f}%")
            with m2: st.metric("Mean Pixel Delta", f"{diff_metric:.1f}")
            with m3: st.metric("Active Restorer", f"{cond_name} U-Net")
        else:
            st.info(
                f"Scene illumination and visibility are optimal (Condition: **{cond_name}**). "
                f"Direct pass-through applied to minimize edge latency without unnecessary restoration overhead."
            )
            st.image(pil_img, caption="Direct Frame (No Restoration Required)", width="stretch")

    # ── Stage Tab 4: YOLO & Monocular Depth ───────────────────────────────────
    with stage_tab4:
        st.markdown("##### Stage 3 & 4 — Object Detection (YOLO11s) & Depth Estimation")
        objs = result.get("objects", [])

        if objs:
            cl1, cl2 = st.columns(2)
            with cl1:
                st.markdown("###### Detected Objects Class Breakdown")
                cls_counts = Counter([o.get("class_name", "object") for o in objs])
                cls_df = pd.DataFrame(list(cls_counts.items()), columns=["Class", "Count"]).set_index("Class")
                st.bar_chart(cls_df, color=["#38bdf8"])
            with cl2:
                st.markdown("###### Detection Confidence Scores")
                conf_scores = [round(o.get("confidence", 0), 2) for o in objs]
                st.dataframe(
                    pd.DataFrame({"Class": [o.get("class_name") for o in objs],
                                  "Track ID": [o.get("track_id") for o in objs],
                                  "Confidence": conf_scores}),
                    hide_index=True,
                    width="stretch"
                )
        else:
            st.info("No road objects detected above the confidence threshold.")

        st.markdown("---")
        st.markdown("###### Monocular Depth Estimation Proximity Map")
        depth_raw = result.get("depth_map")
        if depth_raw is not None:
            depth_vis = colorize_depth_map(depth_raw)
            if depth_vis is not None:
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown("**Original Road Scene**")
                    st.image(pil_img, width="stretch")
                with d2:
                    st.markdown("**Relative Depth Heatmap (Inferno Colormap)**")
                    st.image(depth_vis, width="stretch")
        else:
            st.caption("Depth estimation is currently set to fast mode. Toggle 'Estimate Depth Proximity' above or in the sidebar to compute dense monocular depth maps.")

    # ── Stage Tab 5: Collision Risk Matrix ────────────────────────────────────
    with stage_tab5:
        st.markdown("##### Stage 5 — Situational Collision Risk Engine Telemetry")
        st.caption(
            "Multi-factor safety rule: Risk = Proximity^1.3 x Class Weight x Condition Multiplier x Confidence."
        )
        _render_objects_table(result.get("objects", []))

        with st.expander("Full Telemetry JSON Payload", expanded=False):
            export_payload = {k: v for k, v in result.items() if k not in ["visualization", "enhanced_image", "depth_map"]}
            st.json(export_payload, expanded=False)
            st.download_button(
                "Download Telemetry JSON",
                json.dumps(export_payload, indent=2),
                "frame_telemetry.json",
                mime="application/json",
                key="dl_single_json"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Multi-Image Batch Analysis (Real-Time Live Streaming)
# ══════════════════════════════════════════════════════════════════════════════
def tab_batch(cfg: dict):
    st.markdown("### Multi-Image Fleet Perception & Live Batch Stream")
    st.caption(
        "Process multi-image dashcam datasets in real time. Watch detections, risk scores, and telemetry "
        "update live as each road frame streams through the perception pipeline."
    )

    sample_files = sorted(list(SAMPLES_DIR.glob("*.jpg"))) if SAMPLES_DIR.is_dir() else []

    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        uploaded_files = st.file_uploader(
            "Upload Images (Up to 20 images)",
            type=["jpg", "jpeg", "png", "bmp", "webp"],
            accept_multiple_files=True,
            key="batch_upload"
        )
    with col_b2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if sample_files:
            if st.button("Load Fleet Benchmark (8 Images)", width="stretch", key="btn_load_fleet"):
                st.session_state["fleet_benchmark_active"] = True

    # Determine files to process
    active_files = []
    if uploaded_files:
        active_files = [{"name": f.name, "bytes": f.read()} for f in uploaded_files[:20]]
    elif st.session_state.get("fleet_benchmark_active", False) and sample_files:
        active_files = [{"name": f.name, "bytes": f.read_bytes()} for f in sample_files[:8]]

    if not active_files:
        st.markdown("""
        <div style="border:2px dashed rgba(99,102,241,.3);border-radius:16px;padding:60px 40px;
             text-align:center;margin-top:20px;background:rgba(15,18,28,.5)">
          <div style="font-size:3.5rem;margin-bottom:12px">\U0001f4c1</div>
          <div style="font-size:1.25rem;font-weight:700;color:#e2e8f0;margin-bottom:8px">
            Upload Multiple Dashcam Images or Load Fleet Benchmark Sample</div>
          <div style="color:#94a3b8;font-size:.9rem;max-width:540px;margin:0 auto">
            Stream consecutive road images with live detection overlays, dynamic fleet risk curve,
            class distribution statistics, and CSV report export.
          </div>
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f"Selected **{len(active_files)} frames** for real-time fleet perception analysis.")

    run_batch = st.button("Start Real-Time Fleet Perception", type="primary", width="stretch", key="run_batch_btn")
    if not run_batch:
        return

    with st.spinner("Initializing perception pipeline for fleet processing..."):
        try:
            pipeline = load_pipeline(use_depth=cfg["use_depth"], use_enhancement=cfg["use_enhance"])
        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            return

    # Real-Time Streaming UI Layout
    st.markdown("---")
    st.markdown("#### Real-Time Fleet Perception Stream")
    stream_l, stream_r = st.columns([3, 2])

    with stream_l:
        st.markdown("##### Current Frame Perception Overlay")
        b_frame_ph = st.empty()
        b_caption_ph = st.empty()

    with stream_r:
        st.markdown("##### Live Fleet Telemetry")
        m_c1, m_c2 = st.columns(2)
        b_cond_ph = m_c1.empty()
        b_risk_ph = m_c2.empty()

        m_c3, m_c4 = st.columns(2)
        b_objs_ph = m_c3.empty()
        b_lat_ph  = m_c4.empty()

        b_alert_ph = st.empty()

        st.markdown("###### Dynamic Fleet Risk Score Curve")
        b_risk_chart_ph = st.empty()

    pbar = st.progress(0, text="Streaming fleet frames...")

    batch_results = []
    running_scores = []
    running_indices = []
    t_start_all = time.perf_counter()

    for i, file_obj in enumerate(active_files):
        pbar.progress((i + 1) / len(active_files), text=f"Analyzing Frame {i+1}/{len(active_files)}: {file_obj['name']}...")
        pil_img = Image.open(io.BytesIO(file_obj["bytes"])).convert("RGB")

        try:
            res = pipeline.process_frame(
                pil_img,
                frame_idx=i + 1,
                conf_thresh=cfg["conf_thresh"],
                iou_thresh=cfg["iou_thresh"],
                return_visualization=True
            )
            vis = res.get("visualization", pil_img)
            batch_results.append({"filename": file_obj["name"], "result": res, "pil": pil_img, "ok": True})
        except Exception as exc:
            batch_results.append({"filename": file_obj["name"], "ok": False, "error": str(exc), "pil": pil_img})
            continue

        # ── Real-Time Visual Stream Update ────────────────────────────────────
        b_frame_ph.image(vis, width="stretch")
        r_lvl = res.get("risk_level", "SAFE")
        r_scr = res.get("frame_risk_score", 0.0)
        c_name = res.get("condition", "Day")
        r_col = RISK_COLORS.get(r_lvl, "#22c55e")

        b_caption_ph.markdown(
            f'<div style="text-align:center;font-size:.85rem;font-weight:700;color:{r_col}">'
            f'Frame {i+1}/{len(active_files)}: {file_obj["name"]} &nbsp;|&nbsp; '
            f'{c_name} &nbsp;|&nbsp; {r_lvl} ({r_scr:.3f}) &nbsp;|&nbsp; '
            f'{res.get("detected_objects_count", 0)} objects</div>',
            unsafe_allow_html=True
        )

        b_cond_ph.metric("Condition", c_name)
        b_risk_ph.metric(
            "Collision Risk",
            r_lvl,
            delta=f"{r_scr:.3f}",
            delta_color="inverse" if r_lvl in ["HIGH", "CRITICAL"] else "normal"
        )
        b_objs_ph.metric("Objects", res.get("detected_objects_count", 0))
        b_lat_ph.metric("Latency", f"{res.get('latency_ms', 0):.0f} ms", delta=f"{res.get('fps', 0):.1f} FPS")

        b_css = RISK_CSS.get(r_lvl, "risk-safe")
        b_alert_ph.markdown(
            f'<div class="{b_css}" style="font-size:.85rem;font-weight:700;margin-top:4px">'
            f'{RISK_ICONS.get(r_lvl, "")} {r_lvl} &nbsp; Score: {r_scr:.4f} &nbsp;&middot;&nbsp; '
            f'Critical: {res.get("critical_objects_count", 0)}</div>',
            unsafe_allow_html=True
        )

        running_scores.append(r_scr)
        running_indices.append(f"F{i+1}")
        b_risk_chart_ph.line_chart(
            pd.DataFrame({"Frame": running_indices, "Risk Score": running_scores}).set_index("Frame"),
            color=["#ef4444"]
        )
        time.sleep(0.05)

    pbar.progress(1.0, text="Fleet processing complete!")
    total_elapsed = time.perf_counter() - t_start_all
    avg_fps = len(active_files) / total_elapsed if total_elapsed > 0 else 0.0

    st.success(
        f"Fleet Perception Completed: Processed {len(active_files)} frames in "
        f"{total_elapsed:.1f}s ({avg_fps:.1f} FPS overall throughput)."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # Post-Batch Comprehensive Deep Learning Analytics Dashboard
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### Fleet Analytics & Post-Batch Deep Learning Evaluation")

    ok_results = [r for r in batch_results if r["ok"]]
    if not ok_results:
        st.error("No images could be successfully analyzed.")
        return

    risk_scores = [r["result"].get("frame_risk_score", 0.0) for r in ok_results]
    objects_cnt = [r["result"].get("detected_objects_count", 0) for r in ok_results]
    latencies   = [r["result"].get("latency_ms", 0.0) for r in ok_results]
    high_risk   = sum(1 for r in ok_results if r["result"].get("risk_level") in ["HIGH", "CRITICAL"])
    conditions  = [r["result"].get("condition", "Day") for r in ok_results]
    dom_cond    = Counter(conditions).most_common(1)[0][0]

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: st.metric("Fleet Images", len(ok_results))
    with k2: st.metric("Avg Risk Score", f"{np.mean(risk_scores):.4f}")
    with k3: st.metric("Peak Risk", f"{max(risk_scores):.4f}")
    with k4: st.metric("High-Risk Incidents", f"{high_risk}/{len(ok_results)}")
    with k5: st.metric("Dominant Weather", dom_cond)
    with k6: st.metric("Throughput", f"{avg_fps:.1f} FPS")

    # Multi-class frequency across fleet
    all_fleet_objs = []
    for r in ok_results:
        all_fleet_objs.extend(r["result"].get("objects", []))

    ch_col1, ch_col2 = st.columns(2)
    with ch_col1:
        st.markdown("#### Collision Risk Timeline (Fleet Sequence)")
        f_df = pd.DataFrame({
            "Frame": [f"F{i+1}: {r['filename'][:12]}" for i, r in enumerate(ok_results)],
            "Risk Score": risk_scores
        }).set_index("Frame")
        st.line_chart(f_df, color=["#ef4444"])

    with ch_col2:
        st.markdown("#### Detected Road Object Classes (Fleet Total)")
        if all_fleet_objs:
            fleet_cls_counts = Counter([o.get("class_name", "object") for o in all_fleet_objs])
            st.bar_chart(
                pd.DataFrame(list(fleet_cls_counts.items()), columns=["Class", "Count"]).set_index("Class"),
                color=["#818cf8"]
            )
        else:
            st.caption("No objects detected across the fleet.")

    # Summary Table
    st.markdown("#### Fleet Frame Summary")
    rows = []
    for r in batch_results:
        if r["ok"]:
            res = r["result"]
            rows.append({
                "File": r["filename"],
                "Condition": res.get("condition", "--"),
                "Enhanced": "Yes" if res.get("was_enhanced") else "No",
                "Objects": res.get("detected_objects_count", 0),
                "Critical": res.get("critical_objects_count", 0),
                "Risk Level": res.get("risk_level", "--"),
                "Risk Score": round(res.get("frame_risk_score", 0.0), 4),
                "Latency (ms)": round(res.get("latency_ms", 0.0), 1)
            })
        else:
            rows.append({
                "File": r["filename"],
                "Condition": "ERROR",
                "Enhanced": "--",
                "Objects": 0,
                "Critical": 0,
                "Risk Level": "ERROR",
                "Risk Score": 0.0,
                "Latency (ms)": 0.0
            })

    summary_df = pd.DataFrame(rows)
    st.dataframe(
        summary_df,
        hide_index=True,
        width="stretch",
        column_config={"Risk Score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=1, format="%.4f"
        )}
    )

    st.download_button(
        "Download Complete Fleet CSV Report",
        summary_df.to_csv(index=False),
        "fleet_perception_summary.csv",
        mime="text/csv",
        key="dl_batch_csv"
    )

    # Interactive Filter Gallery
    st.markdown("#### Fleet Result Gallery (With Filter Controls)")
    g_filter = st.selectbox(
        "Filter Gallery By",
        ["All Frames", "High & Critical Risk Only", "Safe & Low Risk Only"],
        key="gallery_filter"
    )

    filtered_results = ok_results
    if g_filter == "High & Critical Risk Only":
        filtered_results = [r for r in ok_results if r["result"].get("risk_level") in ["HIGH", "CRITICAL"]]
    elif g_filter == "Safe & Low Risk Only":
        filtered_results = [r for r in ok_results if r["result"].get("risk_level") in ["SAFE", "LOW"]]

    if filtered_results:
        cols = st.columns(min(4, len(filtered_results)))
        for i, r in enumerate(filtered_results):
            with cols[i % len(cols)]:
                vis = r["result"].get("visualization", r["pil"])
                rl = r["result"].get("risk_level", "")
                rc = RISK_COLORS.get(rl, "#94a3b8")
                st.image(vis, width="stretch")
                st.markdown(
                    f'<div style="text-align:center;margin-top:-6px;padding-bottom:10px">'
                    f'<span style="color:{rc};font-weight:700;font-size:.78rem">'
                    f'{r["filename"]} | {rl} ({r["result"].get("frame_risk_score",0):.3f})'
                    f'</span></div>',
                    unsafe_allow_html=True
                )
    else:
        st.info("No frames match the selected filter criteria.")


# ══════════════════════════════════════════════════════════════════════════════
# High-Speed OpenCV ADAS Overlay Renderer (Live Stream Engine)
# ══════════════════════════════════════════════════════════════════════════════
def draw_fast_adas_overlay_cv2(
    frame_bgr: np.ndarray,
    telemetry: dict,
    live_fps: float = 0.0,
    frame_idx: int = 1,
) -> np.ndarray:
    """
    Renders high-visibility glowing bounding boxes, ByteTrack IDs, distance proximity,
    situational collision risk scores, and glassmorphic ADAS HUD directly in OpenCV (~3ms latency).
    """
    annotated = frame_bgr.copy()
    h, w = annotated.shape[:2]

    # Colors in BGR
    COLOR_SAFE = (0, 220, 100)      # Neon Green
    COLOR_MED  = (0, 175, 255)      # Amber / Orange
    COLOR_CRIT = (35, 35, 240)      # Crimson Red

    # 1. Bounding Boxes & Tracking Pills
    objects = telemetry.get("objects", [])
    for obj in objects:
        bbox = obj.get("bbox", [])
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(0, min(w - 1, x2))
        y2 = max(0, min(h - 1, y2))

        risk = float(obj.get("risk_score", 0.0))
        prox = float(obj.get("proximity", 0.0))
        tid  = obj.get("track_id", "--")
        cname = obj.get("class_name", "obj")
        is_crit = bool(obj.get("is_critical", False))

        box_col = COLOR_CRIT if risk >= 0.70 or is_crit else (COLOR_MED if risk >= 0.40 else COLOR_SAFE)

        # Primary Bounding Box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), box_col, 2, cv2.LINE_AA)

        # High-Tech Corner Brackets
        c_len = max(6, min(16, (x2 - x1) // 4, (y2 - y1) // 4))
        cv2.line(annotated, (x1, y1), (x1 + c_len, y1), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x1, y1), (x1, y1 + c_len), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x2, y1), (x2 - c_len, y1), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x2, y1), (x2, y1 + c_len), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x1, y2), (x1 + c_len, y2), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x1, y2), (x1, y2 - c_len), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x2, y2), (x2 - c_len, y2), box_col, 3, cv2.LINE_AA)
        cv2.line(annotated, (x2, y2), (x2, y2 - c_len), box_col, 3, cv2.LINE_AA)

        # Track Label Pill
        label_text = f"#{tid} {cname} | P:{prox:.2f} | R:{risk:.2f}"
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        tag_y1 = max(0, y1 - th - 7)
        tag_y2 = max(th + 7, y1)
        cv2.rectangle(annotated, (x1, tag_y1), (x1 + tw + 8, tag_y2), box_col, -1)
        cv2.putText(annotated, label_text, (x1 + 4, tag_y2 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. Top ADAS HUD Bar (Glassmorphic)
    overlay = annotated.copy()
    hud_h = 42
    cv2.rectangle(overlay, (0, 0), (w, hud_h), (12, 16, 24), -1)
    cv2.addWeighted(overlay, 0.78, annotated, 0.22, 0, annotated)

    cond_name = telemetry.get("condition", "Day")
    was_enh   = telemetry.get("was_enhanced", False)
    risk_lvl  = telemetry.get("risk_level", "SAFE")
    risk_scr  = float(telemetry.get("frame_risk_score", 0.0))
    crit_cnt  = int(telemetry.get("critical_objects_count", 0))

    hud_status_col = COLOR_CRIT if risk_lvl in ["CRITICAL", "HIGH"] else (COLOR_MED if risk_lvl == "MEDIUM" else COLOR_SAFE)

    # Left: Brand Tag
    cv2.putText(annotated, "ADAPTIVE ROAD VISION | LIVE ADAS", (14, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

    # Center: Condition & Collision Risk
    enh_tag = "[ENHANCED]" if was_enh else "[DIRECT]"
    center_text = f"{cond_name} {enh_tag}  |  RISK: {risk_lvl} ({risk_scr:.2f})"
    (cw, ch), _ = cv2.getTextSize(center_text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
    center_x = max(10, (w - cw) // 2)
    cv2.putText(annotated, center_text, (center_x, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hud_status_col, 2, cv2.LINE_AA)

    # Right: Objects & Live FPS
    right_text = f"Objs: {len(objects)} ({crit_cnt} crit) | {live_fps:.1f} FPS"
    (rw, rh), _ = cv2.getTextSize(right_text, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
    right_x = max(10, w - rw - 14)
    cv2.putText(annotated, right_text, (right_x, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 215, 230), 1, cv2.LINE_AA)

    # 3. Bottom Collision Risk Gauge
    bar_y = h - 6
    gauge_w = int(w * min(1.0, max(0.0, risk_scr)))
    cv2.rectangle(annotated, (0, bar_y), (w, h), (25, 30, 40), -1)
    if gauge_w > 0:
        cv2.rectangle(annotated, (0, bar_y), (gauge_w, h), hud_status_col, -1)

    # 4. Critical Collision Flash Banner
    if risk_lvl in ["CRITICAL", "HIGH"]:
        warn_text = f"COLLISION WARNING - HIGH RISK DETECTED ({risk_scr:.2f})"
        (ww, wh), _ = cv2.getTextSize(warn_text, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 2)
        wx = max(10, (w - ww) // 2)
        cv2.rectangle(annotated, (wx - 14, hud_h + 3), (wx + ww + 14, hud_h + wh + 15), (20, 20, 180), -1)
        cv2.putText(annotated, warn_text, (wx, hud_h + wh + 9), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

    return annotated


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Real-Time Video Processing & Live ADAS Vision
# ══════════════════════════════════════════════════════════════════════════════
def tab_video(cfg: dict):
    st.markdown("### Real-Time Video Processing & Live ADAS Vision")
    st.caption(
        "Continuous real-time video detection stream. Feed road dashcam video or live camera streams "
        "through fine-tuned YOLO11 object detection, ByteTrack ID tracking, atmospheric condition adaptation, "
        "and situational collision risk telemetry."
    )

    # Operational Mode Selector
    mode_col1, mode_col2 = st.columns([2, 1])
    with mode_col1:
        vid_mode = st.radio(
            "Video Perception Engine Mode",
            ["Live Real-Time Detection Feed (Continuous Stream)", "Batch Analysis & MP4 Video Export"],
            horizontal=True,
            key="vid_engine_mode"
        )
    with mode_col2:
        src_mode = st.radio(
            "Video Input Source",
            ["Road Video File", "Live Camera / Webcam Stream"],
            horizontal=True,
            key="vid_src_mode"
        )

    sample_clip_path = RESULTS_DIR / "sample_road_clip.mp4"

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 1: LIVE REAL-TIME DETECTION FEED (PRIMARY USER EXPERIENCE)
    # ──────────────────────────────────────────────────────────────────────────
    if vid_mode == "Live Real-Time Detection Feed (Continuous Stream)":

        # ── Case A: Road Video File Stream ────────────────────────────────────
        if src_mode == "Road Video File":
            col_u1, col_u2 = st.columns([3, 1])
            with col_u1:
                vid_file = st.file_uploader(
                    "Upload Road Dashcam Video (MP4 / AVI / MOV / MKV / WebM)",
                    type=["mp4", "avi", "mov", "mkv", "webm"],
                    key="live_vid_upload"
                )
            with col_u2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if sample_clip_path.is_file():
                    if st.button("Load Demo Road Clip", help="Load built-in 720p road driving clip", key="live_btn_sample"):
                        st.session_state["live_sample_clip_active"] = True

            if vid_file is None and not st.session_state.get("live_sample_clip_active", False):
                st.markdown("""
                <div style="border:2px dashed rgba(99,102,241,.35);border-radius:16px;padding:50px 30px;
                     text-align:center;margin-top:16px;background:rgba(15,18,28,.6)">
                  <div style="font-size:3.5rem;margin-bottom:10px">\U0001f3ac</div>
                  <div style="font-size:1.25rem;font-weight:700;color:#e2e8f0;margin-bottom:6px">
                    Start Live Video Detection
                  </div>
                  <div style="color:#94a3b8;font-size:.9rem;max-width:540px;margin:0 auto">
                    Upload your own road dashcam video or click <b>Load Demo Road Clip</b> to stream
                    live object detection, ByteTrack tracking IDs, and dynamic collision risk telemetry in real time.
                  </div>
                </div>""", unsafe_allow_html=True)
                return

            # Resolve video source bytes
            if vid_file is not None:
                vid_bytes = vid_file.read()
                vid_name = vid_file.name
            else:
                vid_bytes = sample_clip_path.read_bytes()
                vid_name = "sample_road_clip.mp4 (Built-in Demo)"

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_v:
                tmp_v.write(vid_bytes)
                video_file_path = tmp_v.name

            # Live Stream Controls Bar
            st.markdown("---")
            ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 1.4])
            with ctrl_col1:
                start_live = st.button("Start Live Detection Feed", type="primary", use_container_width=True, key="start_live_stream_btn")
            with ctrl_col2:
                stop_live = st.button("Stop Live Stream", type="secondary", use_container_width=True, key="stop_live_stream_btn")
            with ctrl_col3:
                launch_native = st.button("Launch Native Ultra-Fast Window (30+ FPS)", use_container_width=True, key="launch_native_win_btn",
                                          help="Opens a hardware-accelerated DirectX/OpenCV desktop window. Press 'Q' or 'ESC' to exit anytime.")

            # Live Options
            cfg_c1, cfg_c2, cfg_c3, cfg_c4 = st.columns(4)
            with cfg_c1:
                loop_playback = st.toggle("Continuous Loop Playback", value=True, key="live_loop_tog",
                                          help="Seamlessly rewinds and loops video when it reaches the end for continuous live monitoring")
            with cfg_c2:
                speed_sync = st.selectbox("Stream Framerate", ["Natural Video FPS (Real-Time)", "Maximum Speed (Uncapped)"], key="live_speed_sel")
            with cfg_c3:
                res_choice = st.selectbox("Stream Resolution", ["Fast 640p (High-Speed ~25-30 FPS)", "HD 720p", "Native Resolution"], key="live_res_sel")
            with cfg_c4:
                live_enhance = st.toggle("Adaptive Neural Restorer", value=cfg["use_enhance"], key="live_enh_tog",
                                         help="Enhances frames if scene condition is Night, Rain, or Fog")

            # Manage running state
            if stop_live:
                st.session_state["live_video_running"] = False
            if start_live:
                st.session_state["live_video_running"] = True

            # ── Dashboard UI Layout ───────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### Live ADAS Vision Stream")

            # Real-time Telemetry Metrics Row
            m1, m2, m3, m4, m5 = st.columns(5)
            met_cond = m1.empty()
            met_risk = m2.empty()
            met_objs = m3.empty()
            met_fps  = m4.empty()
            met_lat  = m5.empty()

            met_cond.metric("Condition", "--")
            met_risk.metric("Collision Risk", "--")
            met_objs.metric("Road Objects", "--")
            met_fps.metric("Live FPS", "--")
            met_lat.metric("Latency", "--")

            # Video Stream Display Placeholder
            stream_ph = st.empty()
            alert_ph  = st.empty()

            # Dynamic Horizon Chart & Active Objects Table
            chart_col, table_col = st.columns([1.2, 1])
            with chart_col:
                st.markdown("###### Real-Time Collision Risk Horizon (Rolling)")
                chart_ph = st.empty()
            with table_col:
                st.markdown("###### Active Tracked Road Objects Radar")
                table_ph = st.empty()

            # ── Native Window Mode (Hardware-Accelerated OpenCV Window) ────────
            if launch_native:
                with st.spinner("Initializing AI pipeline and launching native window..."):
                    try:
                        pipeline = load_pipeline(use_depth=False, use_enhancement=live_enhance)
                    except Exception as exc:
                        st.error(f"Failed to load pipeline: {exc}")
                        return

                st.info("Native OpenCV window is active! Look at your desktop taskbar. Press **'Q'**, **'ESC'**, or close the window anytime to exit.")

                cap_nat = cv2.VideoCapture(video_file_path)
                nat_fps = cap_nat.get(cv2.CAP_PROP_FPS) or 25.0
                delay_ms = max(1, int(1000.0 / nat_fps)) if speed_sync.startswith("Natural") else 1
                condition_cache = {"cond": "Day", "cnt": 0}
                f_idx = 0

                win_name = "Adaptive Road Vision - Live ADAS Vision Feed [Press Q to Exit]"
                cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

                while cap_nat.isOpened():
                    ret, frame_bgr = cap_nat.read()
                    if not ret:
                        if loop_playback:
                            cap_nat.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        break

                    f_idx += 1
                    t0 = time.perf_counter()

                    # Scale for fast detection
                    if res_choice.startswith("Fast 640p") and frame_bgr.shape[0] > 480:
                        h0, w0 = frame_bgr.shape[:2]
                        frame_proc = cv2.resize(frame_bgr, (640, int(640 * (h0 / w0))), interpolation=cv2.INTER_LINEAR)
                    else:
                        frame_proc = frame_bgr

                    # Condition update
                    if condition_cache["cnt"] % 25 == 0:
                        try:
                            pil_cond = Image.fromarray(cv2.cvtColor(frame_proc, cv2.COLOR_BGR2RGB))
                            c_res = pipeline.predict_condition(pil_cond)
                            condition_cache["cond"] = c_res.get("primary_condition", "Day")
                        except Exception:
                            pass
                    condition_cache["cnt"] += 1
                    cur_cond = condition_cache["cond"]

                    # Object detection & ByteTrack
                    try:
                        yolo_res = pipeline.detector.track(
                            source=frame_proc,
                            conf=cfg["conf_thresh"],
                            iou=cfg["iou_thresh"],
                            persist=True,
                            tracker="bytetrack.yaml",
                            verbose=False
                        )
                        detections = []
                        if yolo_res and len(yolo_res) > 0 and yolo_res[0].boxes is not None:
                            for b in yolo_res[0].boxes:
                                xyxy = b.xyxy[0].cpu().numpy().tolist()
                                conf = float(b.conf[0].item())
                                cid  = int(b.cls[0].item())
                                tid  = int(b.id[0].item()) if b.id is not None else None
                                cname = pipeline.detector.names.get(cid, str(cid))
                                detections.append({
                                    "bbox": xyxy, "confidence": conf, "class_id": cid,
                                    "class_name": cname, "track_id": tid
                                })
                        tracked = pipeline.tracker.update_tracks(detections, frame_idx=f_idx)
                        ph, pw = frame_proc.shape[:2]
                        for det in tracked:
                            bx1, by1, bx2, by2 = det["bbox"]
                            det["proximity"] = min(1.0, max(0.05, (by2 / ph) * ((by2 - by1) / ph) * 2.2))
                        risk_eval = pipeline.risk_engine.evaluate_frame(tracked, condition=cur_cond)
                    except Exception:
                        risk_eval = {"frame_risk_score": 0.0, "risk_level": "SAFE", "objects": [], "critical_objects_count": 0}

                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    live_fps_val = 1000.0 / dt_ms if dt_ms > 0 else 0.0

                    risk_eval["condition"] = cur_cond
                    risk_eval["was_enhanced"] = False
                    annotated_win = draw_fast_adas_overlay_cv2(frame_proc, risk_eval, live_fps=live_fps_val, frame_idx=f_idx)

                    cv2.imshow(win_name, annotated_win)
                    key = cv2.waitKey(delay_ms) & 0xFF
                    if key in [ord("q"), ord("Q"), 27]:
                        break

                cap_nat.release()
                cv2.destroyAllWindows()
                st.success("Native live video window session completed.")
                return

            # ── In-Browser Live Video Detection Stream Loop ────────────────────
            if st.session_state.get("live_video_running", False):
                with st.spinner("Connecting perception pipeline to live video feed..."):
                    try:
                        pipeline = load_pipeline(use_depth=False, use_enhancement=live_enhance)
                    except Exception as exc:
                        st.error(f"Failed to load pipeline: {exc}")
                        return

                cap = cv2.VideoCapture(video_file_path)
                if not cap.isOpened():
                    st.error("Failed to read video stream.")
                    return

                v_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                target_frame_time = 1.0 / v_fps if speed_sync.startswith("Natural") else 0.001

                rolling_risk = deque(maxlen=35)
                rolling_frames = deque(maxlen=35)
                f_num = 0
                condition_cache = {"cond": "Day", "cnt": 0}

                while st.session_state.get("live_video_running", False):
                    t_frame_start = time.perf_counter()
                    ret, frame_bgr = cap.read()
                    if not ret:
                        if loop_playback:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        else:
                            st.info("End of video stream reached.")
                            st.session_state["live_video_running"] = False
                            break

                    f_num += 1

                    # Optional resolution scaling for maximum FPS
                    if res_choice.startswith("Fast 640p") and frame_bgr.shape[0] > 480:
                        h0, w0 = frame_bgr.shape[:2]
                        scaled_w = 640
                        scaled_h = int(640 * (h0 / w0))
                        frame_proc = cv2.resize(frame_bgr, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)
                    elif res_choice.startswith("HD 720p") and frame_bgr.shape[0] > 720:
                        h0, w0 = frame_bgr.shape[:2]
                        scaled_h = 720
                        scaled_w = int(720 * (w0 / h0))
                        frame_proc = cv2.resize(frame_bgr, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)
                    else:
                        frame_proc = frame_bgr

                    # Condition classification (cached every 25 frames for high FPS)
                    if condition_cache["cnt"] % 25 == 0:
                        try:
                            pil_cond = Image.fromarray(cv2.cvtColor(frame_proc, cv2.COLOR_BGR2RGB))
                            cond_pred = pipeline.predict_condition(pil_cond)
                            condition_cache["cond"] = cond_pred.get("primary_condition", "Day")
                        except Exception:
                            pass
                    condition_cache["cnt"] += 1
                    active_cond = condition_cache["cond"]

                    # Object Detection & ByteTrack ID Tracking
                    t_infer_start = time.perf_counter()
                    try:
                        yolo_res = pipeline.detector.track(
                            source=frame_proc,
                            conf=cfg["conf_thresh"],
                            iou=cfg["iou_thresh"],
                            persist=True,
                            tracker="bytetrack.yaml",
                            verbose=False
                        )
                        detections = []
                        if yolo_res and len(yolo_res) > 0 and yolo_res[0].boxes is not None:
                            for b in yolo_res[0].boxes:
                                xyxy = b.xyxy[0].cpu().numpy().tolist()
                                conf = float(b.conf[0].item())
                                cid  = int(b.cls[0].item())
                                tid  = int(b.id[0].item()) if b.id is not None else None
                                cname = pipeline.detector.names.get(cid, str(cid))
                                detections.append({
                                    "bbox": xyxy, "confidence": conf, "class_id": cid,
                                    "class_name": cname, "track_id": tid
                                })

                        tracked_objs = pipeline.tracker.update_tracks(detections, frame_idx=f_num)
                        ph, pw = frame_proc.shape[:2]
                        for det in tracked_objs:
                            bx1, by1, bx2, by2 = det["bbox"]
                            det["proximity"] = min(1.0, max(0.05, (by2 / ph) * ((by2 - by1) / ph) * 2.2))

                        risk_eval = pipeline.risk_engine.evaluate_frame(tracked_objs, condition=active_cond)
                    except Exception as infer_err:
                        risk_eval = {"frame_risk_score": 0.0, "risk_level": "SAFE", "objects": [], "critical_objects_count": 0}

                    infer_ms = (time.perf_counter() - t_infer_start) * 1000.0

                    risk_lvl = risk_eval.get("risk_level", "SAFE")
                    risk_scr = float(risk_eval.get("frame_risk_score", 0.0))
                    crit_cnt = int(risk_eval.get("critical_objects_count", 0))
                    objs_list = risk_eval.get("objects", [])

                    # Frame time and live FPS
                    total_frame_time = time.perf_counter() - t_frame_start
                    live_fps_calc = 1.0 / total_frame_time if total_frame_time > 0 else 0.0

                    # Draw Fast ADAS HUD
                    risk_eval["condition"] = active_cond
                    risk_eval["was_enhanced"] = False
                    annotated_bgr = draw_fast_adas_overlay_cv2(
                        frame_proc, risk_eval, live_fps=live_fps_calc, frame_idx=f_num
                    )

                    # Stream to web interface
                    frame_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                    stream_ph.image(frame_rgb, use_container_width=True)

                    # Update Live KPI Metrics
                    met_cond.metric("Condition", active_cond)
                    met_risk.metric(
                        "Collision Risk",
                        risk_lvl,
                        delta=f"{risk_scr:.3f}",
                        delta_color="inverse" if risk_lvl in ["HIGH", "CRITICAL"] else "normal"
                    )
                    met_objs.metric(
                        "Road Objects",
                        len(objs_list),
                        delta=f"{crit_cnt} Critical" if crit_cnt > 0 else None,
                        delta_color="inverse" if crit_cnt > 0 else "off"
                    )
                    met_fps.metric("Live FPS", f"{live_fps_calc:.1f} FPS")
                    met_lat.metric("Latency", f"{infer_ms:.0f} ms")

                    # Live Collision Risk Alert Banner
                    alert_css = RISK_CSS.get(risk_lvl, "risk-safe")
                    alert_ph.markdown(
                        f'<div class="{alert_css}" style="font-size:.9rem;font-weight:700;margin-top:6px">'
                        f'{RISK_ICONS.get(risk_lvl, "")} <strong>{risk_lvl} RISK</strong> &nbsp;|&nbsp; '
                        f'Collision Score: {risk_scr:.4f} &nbsp;|&nbsp; Active Targets: {len(objs_list)} '
                        f'({crit_cnt} critical threat)</div>',
                        unsafe_allow_html=True
                    )

                    # Update Charts & Tables every 2 frames
                    rolling_risk.append(risk_scr)
                    rolling_frames.append(f"F{f_num}")
                    if f_num % 2 == 0:
                        chart_df = pd.DataFrame({"Frame": list(rolling_frames), "Risk Score": list(rolling_risk)}).set_index("Frame")
                        chart_ph.line_chart(chart_df, color=["#ef4444"])

                        if objs_list:
                            radar_rows = []
                            for o in objs_list[:6]:
                                radar_rows.append({
                                    "ID": o.get("track_id", "--"),
                                    "Class": o.get("class_name", "--"),
                                    "Proximity": f"{o.get('proximity', 0.0):.2f}",
                                    "Risk Score": f"{o.get('risk_score', 0.0):.3f}",
                                    "Critical": "ALERT" if o.get("is_critical") else "Safe"
                                })
                            table_ph.dataframe(pd.DataFrame(radar_rows), hide_index=True, use_container_width=True)

                    # Throttle to natural video speed if enabled
                    elapsed_total = time.perf_counter() - t_frame_start
                    if speed_sync.startswith("Natural") and elapsed_total < target_frame_time:
                        time.sleep(max(0.001, target_frame_time - elapsed_total))

                cap.release()
                st.info("Live video detection stream paused.")

        # ── Case B: Live Camera / Webcam Stream ───────────────────────────────
        elif src_mode == "Live Camera / Webcam Stream":
            st.markdown("##### Live Camera / Webcam Stream Detection")
            cam_c1, cam_c2, cam_c3 = st.columns([1, 1, 1.4])
            with cam_c1:
                cam_idx = st.number_input("Camera Index", min_value=0, max_value=5, value=0, step=1, key="cam_live_idx")
                start_cam = st.button("Start Live Camera Feed", type="primary", use_container_width=True, key="start_cam_btn")
            with cam_c2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                stop_cam = st.button("Stop Camera Feed", type="secondary", use_container_width=True, key="stop_cam_btn")
            with cam_c3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                launch_cam_nat = st.button("Launch Native Camera Window (30+ FPS)", use_container_width=True, key="launch_cam_nat_btn")

            if stop_cam:
                st.session_state["cam_stream_running"] = False
            if start_cam:
                st.session_state["cam_stream_running"] = True

            # Telemetry Metrics Row
            cm1, cm2, cm3, cm4 = st.columns(4)
            c_cond = cm1.empty()
            c_risk = cm2.empty()
            c_objs = cm3.empty()
            c_fps  = cm4.empty()

            cam_stream_ph = st.empty()
            cam_alert_ph  = st.empty()

            if launch_cam_nat:
                with st.spinner("Connecting to camera and launching native window..."):
                    try:
                        pipeline = load_pipeline(use_depth=False, use_enhancement=cfg["use_enhance"])
                    except Exception as exc:
                        st.error(f"Failed to load pipeline: {exc}")
                        return

                cap_cam = cv2.VideoCapture(int(cam_idx))
                if not cap_cam.isOpened():
                    st.error(f"Could not open camera device {cam_idx}.")
                    return

                st.info("Native live camera window is active. Press 'Q' or 'ESC' on the camera window to exit.")
                c_idx = 0
                win_cam_name = f"Camera #{cam_idx} - Live ADAS Vision [Press Q to Exit]"
                cv2.namedWindow(win_cam_name, cv2.WINDOW_NORMAL)

                while cap_cam.isOpened():
                    ret, frame_bgr = cap_cam.read()
                    if not ret:
                        break
                    c_idx += 1
                    t0 = time.perf_counter()

                    frame_proc = cv2.resize(frame_bgr, (640, int(640 * (frame_bgr.shape[0] / frame_bgr.shape[1])))) if frame_bgr.shape[1] > 640 else frame_bgr
                    try:
                        yolo_res = pipeline.detector.track(source=frame_proc, conf=cfg["conf_thresh"], iou=cfg["iou_thresh"], persist=True, tracker="bytetrack.yaml", verbose=False)
                        detections = []
                        if yolo_res and len(yolo_res) > 0 and yolo_res[0].boxes is not None:
                            for b in yolo_res[0].boxes:
                                xyxy = b.xyxy[0].cpu().numpy().tolist()
                                conf = float(b.conf[0].item())
                                cid  = int(b.cls[0].item())
                                tid  = int(b.id[0].item()) if b.id is not None else None
                                cname = pipeline.detector.names.get(cid, str(cid))
                                detections.append({"bbox": xyxy, "confidence": conf, "class_id": cid, "class_name": cname, "track_id": tid})
                        tracked = pipeline.tracker.update_tracks(detections, frame_idx=c_idx)
                        ph, pw = frame_proc.shape[:2]
                        for det in tracked:
                            bx1, by1, bx2, by2 = det["bbox"]
                            det["proximity"] = min(1.0, max(0.05, (by2 / ph) * ((by2 - by1) / ph) * 2.2))
                        risk_eval = pipeline.risk_engine.evaluate_frame(tracked, condition="Day")
                    except Exception:
                        risk_eval = {"frame_risk_score": 0.0, "risk_level": "SAFE", "objects": [], "critical_objects_count": 0}

                    dt = (time.perf_counter() - t0) * 1000.0
                    fps_val = 1000.0 / dt if dt > 0 else 0.0
                    risk_eval["condition"] = "Day"
                    risk_eval["was_enhanced"] = False
                    ann = draw_fast_adas_overlay_cv2(frame_proc, risk_eval, live_fps=fps_val, frame_idx=c_idx)

                    cv2.imshow(win_cam_name, ann)
                    if cv2.waitKey(1) & 0xFF in [ord("q"), ord("Q"), 27]:
                        break

                cap_cam.release()
                cv2.destroyAllWindows()
                st.success("Native camera stream closed.")
                return

            if st.session_state.get("cam_stream_running", False):
                with st.spinner("Connecting to camera device..."):
                    try:
                        pipeline = load_pipeline(use_depth=False, use_enhancement=cfg["use_enhance"])
                    except Exception as exc:
                        st.error(f"Pipeline error: {exc}")
                        return

                cap = cv2.VideoCapture(int(cam_idx))
                if not cap.isOpened():
                    st.error(f"Could not open camera {cam_idx}. Verify that your webcam is connected.")
                    st.session_state["cam_stream_running"] = False
                    return

                c_idx = 0
                while st.session_state.get("cam_stream_running", False):
                    t0 = time.perf_counter()
                    ret, frame_bgr = cap.read()
                    if not ret:
                        st.warning("No frame received from camera.")
                        break

                    c_idx += 1
                    frame_proc = cv2.resize(frame_bgr, (640, int(640 * (frame_bgr.shape[0] / frame_bgr.shape[1])))) if frame_bgr.shape[1] > 640 else frame_bgr

                    try:
                        yolo_res = pipeline.detector.track(
                            source=frame_proc, conf=cfg["conf_thresh"], iou=cfg["iou_thresh"],
                            persist=True, tracker="bytetrack.yaml", verbose=False
                        )
                        detections = []
                        if yolo_res and len(yolo_res) > 0 and yolo_res[0].boxes is not None:
                            for b in yolo_res[0].boxes:
                                xyxy = b.xyxy[0].cpu().numpy().tolist()
                                conf = float(b.conf[0].item())
                                cid  = int(b.cls[0].item())
                                tid  = int(b.id[0].item()) if b.id is not None else None
                                cname = pipeline.detector.names.get(cid, str(cid))
                                detections.append({"bbox": xyxy, "confidence": conf, "class_id": cid, "class_name": cname, "track_id": tid})
                        tracked = pipeline.tracker.update_tracks(detections, frame_idx=c_idx)
                        ph, pw = frame_proc.shape[:2]
                        for det in tracked:
                            bx1, by1, bx2, by2 = det["bbox"]
                            det["proximity"] = min(1.0, max(0.05, (by2 / ph) * ((by2 - by1) / ph) * 2.2))
                        risk_eval = pipeline.risk_engine.evaluate_frame(tracked, condition="Day")
                    except Exception:
                        risk_eval = {"frame_risk_score": 0.0, "risk_level": "SAFE", "objects": [], "critical_objects_count": 0}

                    total_t = time.perf_counter() - t0
                    fps_val = 1.0 / total_t if total_t > 0 else 0.0

                    risk_lvl = risk_eval.get("risk_level", "SAFE")
                    risk_scr = float(risk_eval.get("frame_risk_score", 0.0))
                    objs_list = risk_eval.get("objects", [])

                    risk_eval["condition"] = "Day"
                    risk_eval["was_enhanced"] = False
                    ann = draw_fast_adas_overlay_cv2(frame_proc, risk_eval, live_fps=fps_val, frame_idx=c_idx)

                    cam_stream_ph.image(cv2.cvtColor(ann, cv2.COLOR_BGR2RGB), use_container_width=True)

                    c_cond.metric("Condition", "Day")
                    c_risk.metric("Risk Level", risk_lvl, delta=f"{risk_scr:.3f}", delta_color="inverse" if risk_lvl in ["HIGH", "CRITICAL"] else "normal")
                    c_objs.metric("Road Objects", len(objs_list))
                    c_fps.metric("Live FPS", f"{fps_val:.1f} FPS")

                    time.sleep(0.01)

                cap.release()
                st.info("Live camera session stopped.")

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 2: BATCH ANALYSIS & MP4 VIDEO EXPORT (OFFLINE EXPORT PIPELINE)
    # ──────────────────────────────────────────────────────────────────────────
    else:
        st.markdown("##### Batch Analysis & Annotated MP4 Video Export")
        st.caption("Analyzes the full video file, encodes an annotated H.264 MP4 video with ADAS overlays, and exports comprehensive CSV telemetry reports.")

        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            vid_file = st.file_uploader(
                "Upload Video File (MP4 / AVI / MOV / MKV / WebM)",
                type=["mp4", "avi", "mov", "mkv", "webm"],
                key="batch_vid_upload"
            )
        with col_b2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if sample_clip_path.is_file():
                if st.button("Load Demo Road Clip", help="Test with built-in road driving clip", key="btn_batch_sample_clip"):
                    st.session_state["batch_sample_active"] = True

        if vid_file is None and not st.session_state.get("batch_sample_active", False):
            st.info("Please upload a video or click 'Load Demo Road Clip' above.")
            return

        if vid_file is not None:
            vid_bytes = vid_file.read()
            vid_display_name = vid_file.name
        else:
            vid_bytes = sample_clip_path.read_bytes()
            vid_display_name = "sample_road_clip.mp4 (Built-in Demo)"

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(vid_bytes)
            tmp_path = tmp.name

        cap_info = cv2.VideoCapture(tmp_path)
        total_frames = int(cap_info.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_video = cap_info.get(cv2.CAP_PROP_FPS) or 25.0
        v_width = int(cap_info.get(cv2.CAP_PROP_FRAME_WIDTH))
        v_height = int(cap_info.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_s = total_frames / fps_video if fps_video > 0 else 0.0
        cap_info.release()

        b_c1, b_c2, b_c3 = st.columns(3)
        with b_c1:
            max_f = st.slider("Max Frames to Process", 10, min(1000, max(30, total_frames)), min(120, total_frames), 10, key="b_max_f")
        with b_c2:
            stride = st.slider("Frame Stride (Skip)", 1, 6, 1, 1, key="b_stride")
        with b_c3:
            res_opt = st.selectbox("Resolution Scaling", ["Fast 720p (Scaled)", "Original Resolution", "Ultra-Fast 480p (Scaled)"], key="b_res_opt")

        start_batch_proc = st.button("Start Batch Processing & MP4 Export", type="primary", use_container_width=True, key="start_batch_btn")
        if not start_batch_proc:
            return

        with st.spinner("Initializing perception models for batch rendering..."):
            try:
                pipeline = load_pipeline(use_depth=cfg["use_depth"], use_enhancement=cfg["use_enhance"])
            except Exception as exc:
                st.error(f"Pipeline error: {exc}")
                return

        cap = cv2.VideoCapture(tmp_path)
        out_video_path = str(RESULTS_DIR / f"annotated_video_{int(time.time())}.mp4")
        video_writer = None
        target_fps = max(10.0, fps_video / stride)

        prog_bar = st.progress(0, text="Processing video frames...")
        batch_stream_ph = st.empty()

        f_results = []
        f_images  = []
        processed_cnt = 0
        raw_idx = 0
        t_start = time.perf_counter()

        while processed_cnt < max_f:
            ret, frame_bgr = cap.read()
            if not ret:
                break
            raw_idx += 1
            if (raw_idx - 1) % stride != 0:
                continue

            if res_opt.startswith("Fast 720p") and frame_bgr.shape[0] > 720:
                h, w = frame_bgr.shape[:2]
                frame_bgr = cv2.resize(frame_bgr, (int(w * (720 / h)), 720))
            elif res_opt.startswith("Ultra-Fast 480p") and frame_bgr.shape[0] > 480:
                h, w = frame_bgr.shape[:2]
                frame_bgr = cv2.resize(frame_bgr, (int(w * (480 / h)), 480))

            pil_raw = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            try:
                res = pipeline.process_frame(pil_raw, frame_idx=raw_idx, conf_thresh=cfg["conf_thresh"], iou_thresh=cfg["iou_thresh"], return_visualization=True)
            except Exception:
                processed_cnt += 1
                continue

            vis = res.get("visualization", pil_raw)
            f_results.append(res)
            f_images.append(vis)
            processed_cnt += 1

            if video_writer is None:
                try:
                    video_writer = imageio.get_writer(out_video_path, fps=target_fps, codec="libx264", pixelformat="yuv420p", macro_block_size=None, quality=8)
                except Exception:
                    video_writer = None
            if video_writer is not None:
                try:
                    video_writer.append_data(np.array(vis))
                except Exception:
                    pass

            batch_stream_ph.image(vis, use_container_width=True)
            prog_bar.progress(min(1.0, processed_cnt / max_f), text=f"Processed Frame {raw_idx} ({processed_cnt}/{max_f})...")

        cap.release()
        if video_writer is not None:
            try:
                video_writer.close()
            except Exception:
                pass

        total_t = time.perf_counter() - t_start
        prog_bar.progress(1.0, text="Batch processing complete!")
        st.success(f"Processed {len(f_results)} frames in {total_t:.1f}s ({len(f_results)/total_t:.1f} FPS throughput).")

        out_v_file = Path(out_video_path)
        if out_v_file.is_file() and out_v_file.stat().st_size > 1000:
            st.markdown("#### Annotated Video Playback (.mp4)")
            with open(out_video_path, "rb") as vf:
                out_bytes = vf.read()
            st.video(out_bytes)
            st.download_button(
                "Download Annotated Video (.mp4)",
                data=out_bytes,
                file_name="annotated_road_vision.mp4",
                mime="video/mp4",
                type="primary",
                key="dl_mp4_batch_btn"
            )

        # CSV Export
        csv_rows = []
        for r in f_results:
            csv_rows.append({
                "frame_idx": r.get("frame_idx"),
                "condition": r.get("condition"),
                "was_enhanced": r.get("was_enhanced"),
                "objects_count": r.get("detected_objects_count"),
                "risk_level": r.get("risk_level"),
                "risk_score": r.get("frame_risk_score"),
                "latency_ms": r.get("latency_ms"),
                "fps": r.get("fps"),
            })
        st.download_button(
            "Download Telemetry CSV",
            pd.DataFrame(csv_rows).to_csv(index=False),
            "video_telemetry_report.csv",
            mime="text/csv",
            key="dl_csv_batch_btn"
        )



# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Risk Engine Explorer
# ══════════════════════════════════════════════════════════════════════════════
def tab_risk_explorer():
    st.markdown("### Risk Engine Explorer")
    st.caption("Interactively explore the rule-based risk engine. No model checkpoint required.")

    try:
        from src.risk.risk_engine import RiskEngine
        engine = RiskEngine()
    except Exception as exc:
        st.error(f"Failed to load RiskEngine: {exc}"); return

    col_a, col_b = st.columns(2)
    CLASS_NAMES  = {0:"person",1:"rider",2:"car",3:"truck",4:"bus",
                    5:"train",6:"motorcycle",7:"bicycle",8:"traffic light",9:"traffic sign"}

    with col_a:
        st.markdown("##### Scene Settings")
        condition = st.selectbox("Scene Condition", ["Day","Night","Rain","Fog","Unknown"], key="re_cond")
        n_objects = st.number_input("Number of objects", 1, 10, 3, key="re_n")
        objects = []
        for i in range(int(n_objects)):
            st.markdown(f"###### Object {i+1}")
            c1,c2,c3 = st.columns(3)
            with c1:
                cid = st.selectbox("Class", list(CLASS_NAMES.keys()),
                                   format_func=lambda x: f"{x}: {CLASS_NAMES[x]}",
                                   key=f"re_cls_{i}")
            with c2:
                prox = st.slider("Proximity", 0.0, 1.0, 0.5, 0.05, key=f"re_prox_{i}")
            with c3:
                conf = st.slider("Confidence", 0.0, 1.0, 0.75, 0.05, key=f"re_conf_{i}")
            age = st.slider("Track Age", 1, 20, 5, key=f"re_age_{i}")
            objects.append({"class_id":cid,"class_name":CLASS_NAMES[cid],
                            "proximity":prox,"confidence":conf,"track_age":age})

    with col_b:
        st.markdown("##### Risk Output")
        frame_eval = engine.evaluate_frame(objects, condition=condition)
        risk_level = frame_eval["risk_level"]
        risk_score = frame_eval["frame_risk_score"]

        css = RISK_CSS.get(risk_level,"risk-safe")
        st.markdown(f'<div class="{css}" style="font-size:1rem;font-weight:700;margin-bottom:12px">'
                    f'{RISK_ICONS.get(risk_level,"")} Risk Level: <span style="font-size:1.3rem">'
                    f'{risk_level}</span></div>', unsafe_allow_html=True)

        st.metric("Frame Risk Score",     f"{risk_score:.4f}")
        st.metric("Condition Multiplier", f'x{frame_eval["condition_multiplier"]:.2f}')
        st.metric("Critical Objects",     frame_eval["critical_objects_count"])
        st.progress(min(1.0, risk_score))

        st.markdown("##### Per-Object Scores")
        obj_rows = [{"Class":o.get("class_name",""),
                     "Proximity":f'{o.get("proximity",0):.2f}',
                     "Confidence":f'{o.get("confidence",0):.2f}',
                     "Risk Score":f'{o.get("risk_score",0):.4f}',
                     "Critical":"YES" if o.get("is_critical") else "No"}
                    for o in frame_eval["objects"]]
        st.dataframe(pd.DataFrame(obj_rows), hide_index=True, width="stretch")

        with st.expander("Raw JSON"):
            st.json(frame_eval)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 5 — About
# ══════════════════════════════════════════════════════════════════════════════
# Tab 5 — System Architecture & About
# ══════════════════════════════════════════════════════════════════════════════
def tab_about():
    st.markdown("### System Architecture & Technical Specifications")
    st.caption(
        "Complete technical architecture, multi-modal pipeline workflow, deep learning model inventory, "
        "and mathematical formulations of the Adaptive Road Vision perception framework."
    )

    # ── Executive Hero Banner ─────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(30,35,55,.9) 0%,rgba(15,20,35,.95) 100%);
         border:1px solid rgba(99,102,241,.3);border-radius:16px;padding:26px 32px;margin-bottom:22px;
         box-shadow:0 8px 32px rgba(0,0,0,.35)">
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">
        <span style="font-size:2.2rem">\U0001f6e1\ufe0f</span>
        <div>
          <h2 style="color:#c7d2fe;margin:0;font-size:1.55rem;font-weight:800;letter-spacing:-0.5px">
            Adaptive Road Vision Perception Framework
          </h2>
          <div style="color:#818cf8;font-size:.85rem;font-weight:600">
            End-to-End Multi-Stage Deep Learning &amp; Situational ADAS Risk Intelligence
          </div>
        </div>
      </div>
      <p style="color:#94a3b8;font-size:.9rem;line-height:1.65;margin:8px 0 14px">
        An industrial-grade autonomous vehicle (AV) and advanced driver assistance system (ADAS) perception
        framework designed specifically to overcome catastrophic visual degradation under extreme atmospheric
        and lighting conditions &mdash; including heavy rain, dense fog, low-light night driving, and glare.
        The framework unifies multi-task scene classification, conditional neural image restoration,
        fine-tuned YOLO11s detection, ByteTrack trajectory persistence, monocular depth proximity,
        and transparent situational collision risk telemetry into an ultra-low latency inference engine.
      </p>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        <span style="background:rgba(99,102,241,.18);color:#a5b4fc;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600;border:1px solid rgba(99,102,241,.3)">
          7 Deep Learning Stages
        </span>
        <span style="background:rgba(56,189,248,.18);color:#7dd3fc;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600;border:1px solid rgba(56,189,248,.3)">
          YOLO11s (BDD100K 10-Class)
        </span>
        <span style="background:rgba(34,197,94,.18);color:#86efac;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600;border:1px solid rgba(34,197,94,.3)">
          ByteTrack Kalman Tracking
        </span>
        <span style="background:rgba(234,179,8,.18);color:#fde047;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600;border:1px solid rgba(234,179,8,.3)">
          CycleGAN Domain Adaptation
        </span>
        <span style="background:rgba(244,63,94,.18);color:#fda4af;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:600;border:1px solid rgba(244,63,94,.3)">
          Sub-20ms Edge Throughput
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Architecture Navigation Tabs ──────────────────────────────────────────
    arch_tab1, arch_tab2, arch_tab3, arch_tab4, arch_tab5, arch_tab6 = st.tabs([
        "Full Pipeline Flowchart",
        "7-Stage Deep Learning Pipeline",
        "CycleGAN Domain Adaptation",
        "Model Inventory & Specs",
        "Taxonomy & Risk Engine Formula",
        "Repository & 27 Research Stages",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 1: Full Pipeline Flowchart & Step-by-Step Mermaid Architecture
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab1:
        st.markdown("#### Complete End-to-End System Architecture Specification")
        st.caption(
            "Comprehensive step-by-step architecture mapping the multi-modal perception pipeline from sensory camera ingestion "
            "through condition classification, neural domain adaptation, fine-tuned YOLO11s detection, ByteTrack trajectory tracking, "
            "monocular depth proximity, and the multi-factor situational collision risk engine."
        )

        # ── 1. Live Interactive Mermaid Diagram Render ─────────────────────────
        st.markdown("##### Interactive Visual Architecture Flowchart")

        full_mermaid_code = """flowchart TD
    classDef inputStyle fill:#1e293b,stroke:#64748b,stroke-width:2px,color:#f8fafc;
    classDef stage1Style fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef stage2Style fill:#0c4a6e,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef stage3Style fill:#3b0764,stroke:#c084fc,stroke-width:2px,color:#f8fafc;
    classDef stage4Style fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef stage5Style fill:#713f12,stroke:#facc15,stroke-width:2px,color:#f8fafc;
    classDef stage6Style fill:#4c0519,stroke:#f43f5e,stroke-width:2px,color:#f8fafc;
    classDef stage7Style fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#f8fafc;
    classDef dataStyle fill:#18181b,stroke:#a1a1aa,stroke-width:1px,stroke-dasharray: 4 4,color:#e4e4e7;

    subgraph STEP1 ["STEP 1: SENSORY INGESTION &amp; DATA STREAMING"]
        direction TB
        IN_CAM["Camera Sensors<br/>(Dashcam Video / USB Webcam / RTSP Stream)"]:::inputStyle
        IN_PREPROC["Frame Preprocessor &amp; Normalization<br/>(Resolution: 1080p / 720p / 640p &middot; RGB &middot; Normalized 0.0-1.0)"]:::inputStyle
        IN_CAM --> IN_PREPROC
    end

    subgraph STEP2 ["STEP 2: MULTI-TASK SCENE CONDITION CLASSIFIER"]
        direction TB
        C_IN["Input Tensor Resize: 224 x 224 x 3"]:::stage1Style
        C_BACKBONE["ResNet-18 Backbone Feature Extractor<br/>(Conv1 &rarr; Layers 1-4 &rarr; Global Average Pooling)"]:::stage1Style
        C_HEAD1["Head A: Time-of-Day Classifier<br/>(Day vs. Night) &middot; Binary Softmax"]:::stage1Style
        C_HEAD2["Head B: Weather Classifier<br/>(Clear vs. Rain vs. Fog) &middot; 3-Class Softmax"]:::stage1Style
        C_LOSS["Joint Multi-Task Loss:<br/>L_total = L_time + 1.2 * L_weather"]:::stage1Style
        C_GATE["Confidence Gating &amp; Conditional Routing Signal<br/>(Dominant Scene State &amp; Reliability Metric)"]:::stage1Style
        
        IN_PREPROC --> C_IN
        C_IN --> C_BACKBONE
        C_BACKBONE --> C_HEAD1
        C_BACKBONE --> C_HEAD2
        C_HEAD1 --> C_LOSS
        C_HEAD2 --> C_LOSS
        C_LOSS --> C_GATE
    end

    subgraph STEP3 ["STEP 3: OFFLINE DOMAIN ADAPTATION &amp; DATASET BALANCING"]
        direction TB
        CG_DATA["BDD100K Imbalance: Fog &lt; 0.8% of Total Dataset"]:::dataStyle
        CG_GEN_AB["Generator G_AB: Clear &rarr; Fog<br/>(9 Residual Blocks &middot; Koschmieder Scattering Model)"]:::dataStyle
        CG_GEN_BA["Generator G_BA: Fog &rarr; Clear<br/>(Inverse Dehazing &amp; Structural Reconstruction)"]:::dataStyle
        CG_DISC["PatchGAN Discriminators D_A, D_B<br/>(70x70 Patch Contrast &amp; Fog Realism Evaluation)"]:::dataStyle
        CG_LOSS["Cycle Loss L_cyc + Identity Loss L_idt"]:::dataStyle
        CG_VAL["Quality Gating Filters:<br/>SSIM &ge; 0.72 &amp; High-Frequency Veil-Index Check"]:::dataStyle
        CG_OUT["Balanced Training Split:<br/>final_condition_balanced_v2"]:::dataStyle
        
        CG_DATA --> CG_GEN_AB
        CG_DATA --> CG_GEN_BA
        CG_GEN_AB --> CG_DISC
        CG_GEN_BA --> CG_DISC
        CG_DISC --> CG_LOSS
        CG_LOSS --> CG_VAL
        CG_VAL --> CG_OUT
    end

    subgraph STEP4 ["STEP 4: ADAPTIVE NEURAL RESTORATION ROUTER"]
        direction TB
        R_SWITCH{"Condition Router"}:::stage2Style
        R_NIGHT["Night Enhancer (Residual U-Net)<br/>(Low-Light Illumination Recovery &amp; Anti-Glare)"]:::stage2Style
        R_RAIN["Rain Enhancer (Residual U-Net)<br/>(Streak Removal &amp; Specular Reflection Suppression)"]:::stage2Style
        R_FOG["Fog Enhancer (Dehazing U-Net)<br/>(Transmission Map Inversion &amp; Contrast Recovery)"]:::stage2Style
        R_BYPASS["Zero-Overhead Direct Bypass<br/>(0 ms Latency &amp; Zero Distortion for Day+Clear)"]:::stage2Style
        R_CONVERGE["Normalized Enhanced RGB Frame<br/>(Recovered Edge Textures &amp; Enhanced SNR)"]:::stage2Style

        IN_PREPROC --> R_SWITCH
        C_GATE --> R_SWITCH
        R_SWITCH --> R_NIGHT
        R_SWITCH --> R_RAIN
        R_SWITCH --> R_FOG
        R_SWITCH --> R_BYPASS
        R_NIGHT --> R_CONVERGE
        R_RAIN --> R_CONVERGE
        R_FOG --> R_CONVERGE
        R_BYPASS --> R_CONVERGE
    end

    subgraph STEP5 ["STEP 5: FINE-TUNED YOLO11s MULTI-SCALE DETECTION"]
        direction TB
        D_IN["Scaled Frame: 640 x 640 x 3"]:::stage3Style
        D_BACKBONE["YOLO11s C3k2 Backbone<br/>(Cross-Stage Partial Network &middot; Depthwise Convolutions)"]:::stage3Style
        D_SPPF["SPPF Module (Spatial Pyramid Pooling - Fast)<br/>(Multi-Scale Context Receptive Fields)"]:::stage3Style
        D_HEAD["Anchor-Free Decoupled Head<br/>(Branch 1: DFL BBox Regression &middot; Branch 2: BCE Class Probability)"]:::stage3Style
        D_CLASSES["10 BDD100K Classes:<br/>person, rider, car, truck, bus, train, motorcycle, bicycle, light, sign"]:::stage3Style
        D_NMS["Non-Maximum Suppression (IoU &ge; 0.50 &amp; Conf &ge; 0.25)<br/>Filtered 2D Bounding Boxes (x1, y1, x2, y2, conf, class_id)"]:::stage3Style

        R_CONVERGE --> D_IN
        CG_OUT -.-> D_BACKBONE
        D_IN --> D_BACKBONE
        D_BACKBONE --> D_SPPF
        D_SPPF --> D_HEAD
        D_HEAD --> D_CLASSES
        D_CLASSES --> D_NMS
    end

    subgraph STEP6 ["STEP 6: MONOCULAR DEPTH ESTIMATION &amp; PROXIMITY"]
        direction TB
        DP_IN["Input RGB Frame: 518 x 518"]:::stage5Style
        DP_MODEL["Depth Anything V2 Small Foundation Model<br/>(Vision Transformer &middot; Dense Relative Inverse Depth)"]:::stage5Style
        DP_MAP["Dense Depth Map D(u, v) in range 0.0 to 1.0"]:::stage5Style
        DP_EXTRACT["Ground Contact Plane Quantile Sampling:<br/>Proximity = Quantile_0.30(Depth inside Lower 30% BBox)"]:::stage5Style
        DP_FAST["Fast Geometric Heuristic Fallback:<br/>Prox = min(1.0, (y_bottom/H) * (h_box/H) * 2.2)"]:::stage5Style

        R_CONVERGE --> DP_IN
        DP_IN --> DP_MODEL
        DP_MODEL --> DP_MAP
        DP_MAP --> DP_EXTRACT
        D_NMS --> DP_EXTRACT
        D_NMS --> DP_FAST
    end

    subgraph STEP7 ["STEP 7: BYTETRACK TEMPORAL ASSOCIATION &amp; TRAJECTORY"]
        direction TB
        T_MATCH1["First Association (High-Confidence Detections &gt; 0.50)<br/>IoU Matching with Active Kalman Tracks"]:::stage4Style
        T_MATCH2["Second Association (Low-Confidence Detections 0.10 to 0.50)<br/>Recovers Occluded / Distant Road Users"]:::stage4Style
        T_KALMAN["Kalman Filter Motion State Vector:<br/>(x, y, a, h, vx, vy, va, vh)"]:::stage4Style
        T_PERSIST["Track Memory &amp; ID Persistence (30-Frame Lifespan Buffer)"]:::stage4Style
        T_OUT["Persistent Track Telemetry: (Track ID, Class, Trajectory, Proximity)"]:::stage4Style

        D_NMS --> T_MATCH1
        T_MATCH1 --> T_MATCH2
        T_MATCH1 --> T_KALMAN
        T_MATCH2 --> T_KALMAN
        T_KALMAN --> T_PERSIST
        T_PERSIST --> T_OUT
        DP_EXTRACT --> T_OUT
        DP_FAST --> T_OUT
    end

    subgraph STEP8 ["STEP 8: SITUATIONAL COLLISION RISK ENGINE"]
        direction TB
        R_WEIGHTS["BDD100K Vulnerability Weights W_class:<br/>Person: 1.30, Rider: 1.25, Moto: 1.20, Car: 1.00, Sign: 0.80"]:::stage6Style
        R_COND_MULT["Atmospheric Hazard Multipliers M_cond:<br/>Fog: 1.25x, Night: 1.20x, Rain: 1.15x, Day: 1.00x"]:::stage6Style
        R_FORMULA["Non-Linear Collision Risk Formulation:<br/>Risk_i = (Proximity_i^1.3) * W_class * M_cond * Conf_i * Persist"]:::stage6Style
        R_FRAME["Frame Aggregate Risk:<br/>Frame_Risk = max(Risk_i) + 0.15 * sum(other_risks)"]:::stage6Style
        R_TIERS["5-Tier Safety Alert Hierarchy:<br/>SAFE (&lt;0.25) &middot; LOW (0.25-0.50) &middot; MED (0.50-0.75)<br/>HIGH (0.75-0.88) &middot; CRITICAL (&ge;0.88)"]:::stage6Style

        T_OUT --> R_FORMULA
        R_WEIGHTS --> R_FORMULA
        C_GATE --> R_COND_MULT
        R_COND_MULT --> R_FORMULA
        R_FORMULA --> R_FRAME
        R_FRAME --> R_TIERS
    end

    subgraph STEP9 ["STEP 9: REAL-TIME ADAS HUD &amp; DRIVER WARNING TELEMETRY"]
        direction TB
        HUD_RENDER["High-Speed OpenCV Overlay Kernel: draw_fast_adas_overlay_cv2<br/>(Latency &lt; 3 ms &middot; Anti-Aliased Direct Frame Buffer)"]:::stage7Style
        HUD_VISUAL["HUD Visual Overlay Features:<br/>- Dynamic Color Boxes (Green: Safe, Amber: Med, Crimson: High)<br/>- Track Pills: TrackID, Class, Distance, Risk Score<br/>- Glassmorphic Top Telemetry Bar &amp; Bottom Risk Gauge"]:::stage7Style
        HUD_ALERT["Acoustic &amp; Optical Driver Warning System:<br/>Flashing Collision Warning Banner upon CRITICAL Risk (&ge;0.88)"]:::stage7Style
        HUD_OUTPUT["Dual Deployment Targets:<br/>1. Interactive Streamlit Web App (Localhost:8501)<br/>2. Native DirectX/OpenCV Ultra-Fast Window (30+ FPS Zero Latency)"]:::stage7Style

        R_CONVERGE --> HUD_RENDER
        R_TIERS --> HUD_RENDER
        T_OUT --> HUD_RENDER
        HUD_RENDER --> HUD_VISUAL
        HUD_VISUAL --> HUD_ALERT
        HUD_ALERT --> HUD_OUTPUT
    end"""

        # JSON-encode to pass safely into JavaScript without HTML tag mangling
        mermaid_json = json.dumps(full_mermaid_code)

        mermaid_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      background: #0b0f19;
      color: #f8fafc;
      margin: 0;
      padding: 16px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow-x: auto;
    }}
    #graph-wrap {{
      display: flex;
      justify-content: center;
      min-width: 1100px;
    }}
    svg {{
      max-width: 100% !important;
      height: auto !important;
    }}
  </style>
</head>
<body>
  <div id="graph-wrap">
    <div id="mermaid-target" style="width: 100%; display: flex; justify-content: center;">
      <div style="color: #818cf8; font-size: 14px; padding: 20px;">Rendering architecture diagram...</div>
    </div>
  </div>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: true
      }},
      themeVariables: {{
        darkMode: true,
        background: '#0b0f19',
        primaryColor: '#312e81',
        primaryTextColor: '#f8fafc',
        primaryBorderColor: '#818cf8',
        lineColor: '#38bdf8',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a'
      }}
    }});

    const graphCode = {mermaid_json};

    async function drawGraph() {{
      try {{
        const target = document.getElementById('mermaid-target');
        const {{ svg }} = await mermaid.render('mermaid-chart-svg', graphCode);
        target.innerHTML = svg;
      }} catch (err) {{
        console.error('Mermaid render error:', err);
        const target = document.getElementById('mermaid-target');
        target.innerHTML = '<div style="color:#ef4444;background:rgba(239,68,68,0.12);border:1px solid #ef4444;border-radius:8px;padding:16px;">' +
                           '<strong>Diagram Render Warning:</strong> ' + err.message + '</div>';
      }}
    }}
    drawGraph();
  </script>
</body>
</html>"""
        components.html(mermaid_html, height=1050, scrolling=True)

        # ── 2. Step-by-Step Architectural Walkthrough ─────────────────────────
        st.markdown("---")
        st.markdown("##### Step-by-Step Architectural Walkthrough")
        st.caption("Detailed walkthrough of every stage, model architecture, tensor transformation, and loss function:")

        step_t1, step_t2, step_t3, step_t4 = st.tabs([
            "Steps 1-2: Ingestion & Classifier",
            "Steps 3-4: Domain Adaptation & U-Nets",
            "Steps 5-6: YOLO11s & Depth Estimation",
            "Steps 7-9: Tracking, Risk Engine & HUD",
        ])

        with step_t1:
            st.markdown(r"""
            ###### Step 1: Sensory Ingestion & Frame Normalization
            - **Input Modalities**: Road video files (MP4, AVI, MKV, WebM), live connected USB/onboard webcams, or camera stream frames.
            - **Optical Ingestion**: Resolution extracted at native $1920 \times 1080$ or $1280 \times 720$ px; normalized from $[0, 255]$ uint8 to $[0.0, 1.0]$ float32 RGB tensor.
            - **Throughput Optimization**: Fast scaling to $640\text{p}$ inference resolution preserving spatial aspect ratio and multi-scale road textures.

            ###### Step 2: Multi-Task Scene Condition Classifier (ResNet-18)
            - **Backbone**: ResNet-18 feature extractor stripped of standard pooling.
            - **Input Tensor**: $224 \times 224 \times 3$ normalized with ImageNet statistics ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
            - **Decoupled Classification Heads**:
              - **Time Head (Binary)**: Linear projection to 2 logits $\to$ Softmax ($P(\text{Day}), P(\text{Night})$).
              - **Weather Head (3-Class)**: Linear projection to 3 logits $\to$ Softmax ($P(\text{Clear}), P(\text{Rain}), P(\text{Fog})$).
            - **Multi-Task Objective**:
              $$\mathcal{L}_{\text{condition}} = \mathcal{L}_{\text{CE}}(\hat{y}_{\text{time}}, y_{\text{time}}) + 1.2 \times \mathcal{L}_{\text{CE}}(\hat{y}_{\text{weather}}, y_{\text{weather}})$$
            - **Gating Signal**: Generates the routing indicator determining which restorative CNN is triggered in Step 4.
            """)

        with step_t2:
            st.markdown(r"""
            ###### Step 3: Offline CycleGAN Domain Adaptation & Dataset Balancing
            - **Adverse Weather Scarcity Problem**: BDD100K contains $<0.8\%$ real fog frames. Standard detectors fail on foggy driving scenes due to contrast collapse.
            - **Adversarial Synthesis Architecture**:
              - **Generators**: $G: \text{Clear} \to \text{Fog}$ and $F: \text{Fog} \to \text{Clear}$ built with 9 residual blocks and Instance Normalization.
              - **Discriminators**: $D_{\text{Fog}}$ and $D_{\text{Clear}}$ ($70 \times 70$ PatchGAN evaluating local textural authenticity).
            - **Loss Formulation**:
              $$\mathcal{L}_{\text{CycleGAN}} = \mathcal{L}_{\text{GAN}}(G, D_{\text{Fog}}) + \mathcal{L}_{\text{GAN}}(F, D_{\text{Clear}}) + \lambda_{\text{cyc}}\mathcal{L}_{\text{cyc}}(G, F) + \lambda_{\text{idt}}\mathcal{L}_{\text{idt}}(G, F)$$
            - **Automated Quality Verification**: All synthetic foggy frames pass **SSIM $\ge 0.72$** (bounding box structure preservation) and **Veil Index** gradient scattering verification to produce the balanced `final_condition_balanced_v2` dataset.

            ###### Step 4: Adaptive Neural Restoration Router (Residual U-Nets)
            - **Dynamic Conditional Router**: Evaluates Step 2 output to select the optimal restorative branch:
              - **Night Enhancer**: 5-stage Residual U-Net with skip connections. Boosts low-light shadow dynamic range without saturating oncoming headlight glare.
              - **Rain Enhancer**: High-pass residual U-Net removing rain streaks and asphalt water-film reflections.
              - **Fog Enhancer**: Trained on CycleGAN fog pairs. Inverts Koschmieder's Law ($I(x) = J(x)t(x) + A(1 - t(x))$) to reconstruct clean road reflectance $J(x)$.
              - **Day+Clear Bypass**: If scene is optimal, frame bypasses enhancement with **$0\text{ ms}$ latency overhead** and zero pixel distortion.
            """)

        with step_t3:
            st.markdown(r"""
            ###### Step 5: Fine-Tuned YOLO11s Multi-Scale 2D Object Detection
            - **Backbone**: Ultralytics **YOLO11s** with C3k2 cross-stage partial blocks and depthwise separable convolutions.
            - **Receptive Field**: SPPF (Spatial Pyramid Pooling - Fast) pooling across $\{5 \times 5, 9 \times 9, 13 \times 13\}$ kernel scales, capturing distant pedestrians and near-field semi-trucks simultaneously.
            - **Decoupled Anchor-Free Detection Head**:
              - **Regression Head**: Distribution Focal Loss (DFL) estimating continuous bounding box distribution offsets $[x_1, y_1, x_2, y_2]$.
              - **Classification Head**: Binary Cross-Entropy (BCE) loss across 10 BDD100K road classes.
            - **Inference Optimization**: Post-processed via Non-Maximum Suppression (NMS) with $IoU \ge 0.50$ and Confidence threshold $Conf \ge 0.25$.

            ###### Step 6: Monocular Depth Estimation & Proximity Sensing
            - **Foundation Model**: **Depth Anything V2 (Small)** predicting dense relative monocular inverse depth $D(u, v) \in [0.0, 1.0]$.
            - **Road Contact Quantile Sampling**: Rather than averaging entire bounding boxes (which skew toward background sky or buildings), the system samples the lower 30% vertical quantile of each detected box:
              $$\text{Proximity}_i = \text{Quantile}_{0.30}\Big(\{D(u, v) \mid (u, v) \in B_{i, \text{lower}}\}\Big)$$
            - **High-Speed Geometric Fallback**: When running in ultra-fast edge mode, proximity is computed in $<0.1\text{ ms}$ via perspective projection geometry:
              $$\text{Proximity}_{\text{fast}} = \min\left(1.0, \frac{y_{\text{bottom}}}{H} \times \frac{h_{\text{box}}}{H} \times 2.2\right)$$
            """)

        with step_t4:
            st.markdown(r"""
            ###### Step 7: ByteTrack Multi-Object Tracking & Kalman Association
            - **Temporal Continuity Problem**: Frame-by-frame detection suffers from flickering boxes, occlusion dropouts, and ID switching.
            - **Two-Stage Matching Algorithm**:
              1. **High-Confidence Matching**: Associates confident detections ($Conf > 0.50$) with active Kalman tracks using IoU distance.
              2. **Low-Confidence Matching**: Matches remaining unmatched tracks with low-confidence detections ($0.10 \le Conf \le 0.50$) to recover occluded road users.
            - **8-State Kalman Motion Vector**: $[x, y, a, h, \dot{x}, \dot{y}, \dot{a}, \dot{h}]$ modeling 2D bounding box center coordinates, aspect ratio, height, and respective instantaneous velocities.
            - **Track Persistence Buffer**: 30-frame memory window preserving object identity across roadside obstruction.

            ###### Step 8: Multi-Factor Situational Collision Risk Engine
            - **Transparent Physics & Policy Formulation**:
              $$\text{Risk}_i = \left(\text{Proximity}_i\right)^{1.3} \times W_{\text{class}}[\text{class}_i] \times M_{\text{condition}}[\text{cond}] \times \text{Confidence}_i \times P_{\text{persistence}}$$
            - **Non-Linear Exponent ($1.3$)**: Creates exponential urgency as obstacles enter the near-field collision zone ($< 15\text{m}$).
            - **Vulnerability Weights ($W_{\text{class}}$)**: Person ($1.30$), Rider ($1.25$), Motorcycle ($1.20$), Car ($1.00$), Traffic Sign ($0.80$).
            - **Hazard Multipliers ($M_{\text{cond}}$)**: Fog ($1.25\times$), Night ($1.20\times$), Rain ($1.15\times$), Day ($1.00\times$).
            - **Frame Aggregation**:
              $$\text{FrameRisk} = \max_{i}(\text{Risk}_i) + 0.15 \times \sum_{j \neq \text{argmax}} \text{Risk}_j$$
            - **5 Alert Tiers**: **SAFE** ($<0.25$), **LOW** ($0.25-0.50$), **MEDIUM** ($0.50-0.75$), **HIGH** ($0.75-0.88$), **CRITICAL** ($\ge 0.88$).

            ###### Step 9: Real-Time HUD Visualization & Driver Warning Telemetry
            - **Ultra-Fast OpenCV Kernel (`draw_fast_adas_overlay_cv2`)**: Executes in $<3\text{ ms}$ on the raw frame buffer with zero serialization overhead.
            - **Dynamic Visual Cues**: Neon green (SAFE), amber (MEDIUM), crimson red (HIGH/CRITICAL) bounding boxes with target telemetry pills (`#ID`, `Class`, `Proximity`, `Risk Score`).
            - **Dual Operational Deployment**:
              - In-Browser Web Stream on Streamlit (`http://localhost:8501`).
              - Hardware-Accelerated Native OpenCV/DirectX Desktop Window ($30+\text{ FPS}$ zero-latency live stream).
            """)

        # ── 3. Copyable Raw Mermaid Code ──────────────────────────────────────
        with st.expander("View / Copy Complete Raw Mermaid Architecture Code (GitHub & Markdown Ready)", expanded=False):
            st.code(full_mermaid_code, language="mermaid")


    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 2: 7-Stage Deep Learning Pipeline
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab2:
        st.markdown("#### Comprehensive Breakdown of the 7 Perception Stages")

        with st.expander("Stage 1 — Multi-Task Condition Classifier (ResNet-18)", expanded=True):
            st.markdown(r"""
            - **Backbone Architecture**: ResNet-18 pretrained on ImageNet, stripped of its original classification head.
            - **Input**: 224 &times; 224 RGB image normalized with ImageNet mean and variance.
            - **Multi-Task Decoupled Heads**:
              - **Time Head**: Binary classification (`Day` vs. `Night`) with Cross-Entropy loss.
              - **Weather Head**: 3-class classification (`Clear`, `Rain`, `Fog`) with Cross-Entropy loss.
              - **Joint Loss Function**: $\mathcal{L}_{total} = \mathcal{L}_{time} + 1.2 \cdot \mathcal{L}_{weather}$.
            - **Inference Latency**: $\approx 4.2\text{ ms}$ on GPU ($\approx 18\text{ ms}$ on CPU).
            - **Gating Mechanism**: Outputs softmax probability vectors and an overall confidence score. If weather is classified as Day+Clear with $>85\%$ confidence, Stage 2 bypasses enhancement entirely.
            """)

        with st.expander("Stage 2 — Adaptive Neural Restoration Suite (Residual U-Net CNNs)", expanded=True):
            st.markdown(r"""
            - **Design Philosophy**: Instead of feeding raw degraded pixels to YOLO (causing catastrophic false negatives), scene-specific neural restorers reconstruct normalized reflectance and remove atmospheric veils.
            - **Sub-Model Architectures**:
              - **Night Enhancer**: 5-level Residual U-Net with skip connections, trained on synthetic and paired dark/bright road driving pairs. Boosts underexposed shadows without blowing out high-beam headlights.
              - **Rain Enhancer**: U-Net with high-pass residual learning. Suppresses vertical rain streaks, water film specular reflections, and lens droplets.
              - **Fog Enhancer**: Trained on CycleGAN-synthesized foggy road scenes. Reconstructs atmospheric transmission maps according to Koschmieder's Law ($I(x) = J(x)t(x) + A(1-t(x))$) to invert haze.
            - **Dynamic Direct Bypass**: Optimal day/clear frames bypass enhancement with $0\text{ ms}$ overhead, preserving edge frame-rate.
            """)

        with st.expander("Stage 3 — Object Detection (Fine-Tuned YOLO11s)", expanded=True):
            st.markdown(r"""
            - **Model Selection**: Ultralytics **YOLO11s** selected over YOLO11n following rigorous benchmarking on BDD100K validation and test splits (mAP@50: **61.4%**, mAP@50-95: **38.8%**).
            - **Architectural Enhancements**:
              - **C3k2 Backbone**: Efficient cross-stage partial network blocks with depthwise separable convolutions for high feature discriminability.
              - **SPPF (Spatial Pyramid Pooling - Fast)**: Captures multi-scale contextual receptive fields critical for detecting small distant pedestrians and large oncoming trucks simultaneously.
              - **Decoupled Anchor-Free Head**: Independent branches for objectness, bounding box regression (DFL - Distribution Focal Loss), and class classification (BCE Loss).
            - **Taxonomy**: 10 road classes: `person`, `rider`, `car`, `truck`, `bus`, `train`, `motorcycle`, `bicycle`, `traffic light`, `traffic sign`.
            """)

        with st.expander("Stage 4 — Multi-Object Tracking & Trajectory Continuity (ByteTrack)", expanded=True):
            st.markdown(r"""
            - **Problem Solved**: Standard frame-by-frame object detectors discard low-confidence detections, leading to track fragmentation and ID switching during turns or partial occlusion.
            - **ByteTrack Two-Stage Matching Algorithm**:
              1. **High-Confidence Matching**: Associates detections with confidence $> 0.5$ against active Kalman filter predicted tracks using IoU distance.
              2. **Low-Confidence Matching**: Associates remaining unmatched tracks against low-confidence detections ($0.1 < \text{conf} \le 0.5$) to recover partially occluded road users.
            - **Kalman Filter**: 8-dimensional state vector $[x, y, a, h, \dot{x}, \dot{y}, \dot{a}, \dot{h}]$ modeling 2D bounding box center, aspect ratio, height, and their respective velocities.
            - **Track Persistence**: Configured with a lifespan buffer of 30 frames to handle brief roadside obstruction.
            """)

        with st.expander("Stage 5 — Monocular Depth Estimation & Proximity Sensing", expanded=True):
            st.markdown(r"""
            - **Model**: **Depth Anything V2 (Small)** foundation model fine-tuned for dense relative monocular depth estimation.
            - **Geometric Proximity Extraction**:
              - Computes the dense inverse depth map $D(u, v) \in [0, 1]$.
              - Samples the lower 30% quantile of each detected 2D bounding box to estimate road ground contact point depth:
                $$\text{Proximity}(B) = \text{Quantile}_{0.30}\Big(\{D(u, v) \mid (u, v) \in B_{lower}\}\Big)$$
            - **Fast Heuristic Fallback**: In high-speed edge streaming mode where Depth Anything V2 is toggled off, proximity is computed using perspective camera geometry and normalized bounding box vertical position:
              $$\text{Proximity}_{fast} = \min\left(1.0, \frac{y_{bottom}}{H} \times \frac{h_{box}}{H} \times 2.2\right)$$
            """)

        with st.expander("Stage 6 — Multi-Factor Situational Collision Risk Engine", expanded=True):
            st.markdown(r"""
            - **Objective**: Replace black-box neural risk predictions with an interpretable, transparent physics-and-policy rule engine.
            - **Mathematical Formulation**:
              $$\text{Risk}_i = \left(\text{Proximity}_i\right)^{1.3} \times W_{\text{class}}[\text{class}_i] \times M_{\text{condition}}[\text{cond}] \times \text{Confidence}_i \times P_{\text{persistence}}$$
            - **Non-Linear Exponent ($1.3$)**: Creates exponential urgency as an obstacle enters the near-field collision zone ($< 15\text{m}$).
            - **Frame Aggregation**:
              $$\text{FrameRisk} = \max_{i}\left(\text{Risk}_i\right) + 0.15 \times \sum_{j \neq \text{argmax}} \text{Risk}_j$$
            - **5-Tier Operational Safety Alert Hierarchy**:
              - **SAFE** ($< 0.25$): Normal highway driving, clear lane ahead.
              - **LOW** ($0.25 - 0.50$): Distant traffic or non-hazardous stationary objects.
              - **MEDIUM** ($0.50 - 0.75$): Approaching traffic, lane changes, or wet road surface.
              - **HIGH** ($0.75 - 0.88$): Close proximity obstacle or vulnerable road user in path.
              - **CRITICAL** ($\ge 0.88$): Imminent collision threat &mdash; immediate emergency braking or steering intervention required.
            """)

        with st.expander("Stage 7 — Real-Time ADAS HUD & Driver Warning Visualization Engine", expanded=True):
            st.markdown(r"""
            - **Direct Frame-Buffer Rendering**: High-speed OpenCV drawing kernel (`draw_fast_adas_overlay_cv2`) executing in under $3\text{ ms}$.
            - **Visual Elements**:
              - **Color-Coded Dynamic Bounding Boxes**: Neon green for safe targets, amber for elevated risk, crimson red for critical hazards.
              - **Anti-Aliased Target Pills**: Bounding box banners showing `#TrackID`, `Class`, `Proximity`, and `Risk Score`.
              - **Glassmorphic Top HUD Bar**: Real-time scene status badge, dominant condition, risk tier, active target count, and live inference FPS.
              - **Bottom Risk Gauge**: Proportional gradient telemetry bar illustrating aggregate frame collision urgency.
              - **Flashing Critical Alert**: Full-width high-urgency audio/visual warning when collision risk crosses $0.88$.
            """)

    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 3: CycleGAN Domain Adaptation
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab3:
        st.markdown("#### CycleGAN Unpaired Domain Adaptation for Extreme Fog Synthesis")
        st.caption("How the system overcomes extreme data scarcity in autonomous driving datasets:")

        col_cg1, col_cg2 = st.columns([1.2, 1])
        with col_cg1:
            st.markdown(r"""
            ##### The Severe Adverse Weather Data Scarcity Problem
            In standard autonomous driving benchmarks like **BDD100K**, real-world driving frames with dense fog represent
            **less than 0.8% of the total dataset**. Training a deep learning object detector directly on such imbalanced data causes:
            1. Extreme class recall collapse during heavy fog.
            2. High false alarm rates caused by headlight backscattering.
            3. Inability of restoration networks to distinguish between white vehicles and atmospheric haze.

            ##### CycleGAN Architecture & Training Strategy
            To resolve this, we trained an **Unpaired Cycle-Consistent Generative Adversarial Network (CycleGAN)**:
            - **Source Domain $\mathcal{X}$**: Clear Day/Night driving scenes ($> 15,000$ images).
            - **Target Domain $\mathcal{Y}$**: True adverse foggy road driving frames.
            - **Generators**:
              - $G: \mathcal{X} \to \mathcal{Y}$ (Synthesizes realistic atmospheric scattering and attenuation onto clear roads).
              - $F: \mathcal{Y} \to \mathcal{X}$ (Dehazes and reconstructs clean road textures from foggy scenes).
              - Architecture: 9 Residual Blocks with Instance Normalization and reflection padding.
            - **Discriminators**:
              - $D_{\mathcal{X}}$ and $D_{\mathcal{Y}}$: $70 \times 70$ PatchGAN discriminators evaluating local texture realism.
            """)
        with col_cg2:
            st.markdown(r"""
            ##### Mathematical Objective Function
            The full objective combines adversarial loss with cycle-consistency and identity mapping losses:
            $$\mathcal{L} = \mathcal{L}_{GAN}(G, D_Y) + \mathcal{L}_{GAN}(F, D_X) + \lambda_{cyc}\mathcal{L}_{cyc}(G, F) + \lambda_{idt}\mathcal{L}_{idt}(G, F)$$
            Where:
            $$\mathcal{L}_{cyc} = \mathbb{E}[\|F(G(x)) - x\|_1] + \mathbb{E}[\|G(F(y)) - y\|_1]$$

            ##### Synthetic Fog Verification Filters
            Before synthetic images are admitted into the final balanced training split (`final_condition_balanced_v2`), they pass two automated quality checks:
            1. **SSIM Structural Conservation**: Bounding box region SSIM $> 0.72$ to ensure object geometries (cars, pedestrians) are never altered or hallucinated.
            2. **Veil Index Metric**: High-frequency gradient attenuation verification ensuring synthetic fog accurately adheres to Koschmieder's physical scattering model.
            """)

    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 4: Model Inventory & Technical Specs
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab4:
        st.markdown("#### Comprehensive Deep Learning Model Inventory")
        st.caption("Active models, network backbones, training data, input resolutions, and latency benchmarks:")

        model_matrix = [
            {
                "Module": "Condition Classifier",
                "Backbone": "ResNet-18 (Multi-Task)",
                "Input Dim": "224 x 224 x 3",
                "Training Dataset": "BDD100K Condition Labels (15,000)",
                "Output / Targets": "Time: Day/Night | Weather: Clear/Rain/Fog",
                "Weights Path": "models/condition/condition_multitask_best.pth",
                "Latency (GPU)": "4.2 ms",
                "Parameters": "11.2M",
            },
            {
                "Module": "Night Enhancer",
                "Backbone": "Residual U-Net (5-Stage)",
                "Input Dim": "Dynamic (640-1080p)",
                "Training Dataset": "Synthetic Low-Light Driving Pairs",
                "Output / Targets": "Restored Low-Light Reflection Image",
                "Weights Path": "models/enhancement/night/night_enhancer_best.pth",
                "Latency (GPU)": "12.8 ms",
                "Parameters": "7.8M",
            },
            {
                "Module": "Rain Enhancer",
                "Backbone": "Residual U-Net (5-Stage)",
                "Input Dim": "Dynamic (640-1080p)",
                "Training Dataset": "Synthetic Streak & Specular Pairs",
                "Output / Targets": "De-Rained Clean Road Image",
                "Weights Path": "models/enhancement/rain/rain_enhancer_best.pth",
                "Latency (GPU)": "13.1 ms",
                "Parameters": "7.8M",
            },
            {
                "Module": "Fog Enhancer",
                "Backbone": "Residual U-Net (5-Stage)",
                "Input Dim": "Dynamic (640-1080p)",
                "Training Dataset": "CycleGAN Paired Foggy Road Dataset",
                "Output / Targets": "Dehazed High-Contrast Road Image",
                "Weights Path": "models/enhancement/fog/fog_enhancer_best.pth",
                "Latency (GPU)": "12.9 ms",
                "Parameters": "7.8M",
            },
            {
                "Module": "CycleGAN Generator",
                "Backbone": "9-ResBlock ResNet",
                "Input Dim": "256 x 256 x 3",
                "Training Dataset": "BDD100K Day & True Foggy Unpaired",
                "Output / Targets": "Synthesized Realistic Foggy Domain",
                "Weights Path": "models/cyclegan/G_AB_best.pth",
                "Latency (GPU)": "Offline / Training",
                "Parameters": "11.4M",
            },
            {
                "Module": "Object Detector",
                "Backbone": "YOLO11s (C3k2 + SPPF)",
                "Input Dim": "640 x 640 x 3",
                "Training Dataset": "final_condition_balanced_v2 (10-Class)",
                "Output / Targets": "2D Bounding Boxes + 10 Road Classes",
                "Weights Path": "models/detection/final_selected_detector.pt",
                "Latency (GPU)": "7.8 ms",
                "Parameters": "9.4M",
            },
            {
                "Module": "Multi-Object Tracker",
                "Backbone": "ByteTrack + Kalman Filter",
                "Input Dim": "Bounding Box Telemetry",
                "Training Dataset": "Deterministic Trajectory Association",
                "Output / Targets": "Persistent Track IDs & Velocity Vectors",
                "Weights Path": "Pure Algorithm / No Checkpoint",
                "Latency (GPU)": "1.2 ms",
                "Parameters": "N/A",
            },
            {
                "Module": "Monocular Depth",
                "Backbone": "Depth Anything V2 (Small)",
                "Input Dim": "518 x 518 x 3",
                "Training Dataset": "Large-Scale Monocular Foundation",
                "Output / Targets": "Dense Relative Inverse Depth Map",
                "Weights Path": "HuggingFace / PyTorch Hub",
                "Latency (GPU)": "14.5 ms",
                "Parameters": "24.8M",
            },
            {
                "Module": "Risk Engine",
                "Backbone": "Multi-Factor Rule Engine",
                "Input Dim": "Tracked Detections + Condition",
                "Training Dataset": "Physical ADAS Safety Formulation",
                "Output / Targets": "Frame Risk Score [0,1] & Alert Tier",
                "Weights Path": "Pure Algorithm (src/risk/risk_engine.py)",
                "Latency (GPU)": "0.3 ms",
                "Parameters": "N/A",
            },
        ]

        st.dataframe(pd.DataFrame(model_matrix), hide_index=True, width="stretch")

    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 5: Taxonomy & Risk Engine Formula
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab5:
        st.markdown("#### BDD100K Detection Taxonomy & Risk Engine Formulation")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("##### BDD100K 10-Class Detection Taxonomy")
            tax_rows = [
                {"Class ID": 0, "Name": "person", "Weight": 1.30, "Vulnerability Profile": "Highest vulnerability: unprotected pedestrian."},
                {"Class ID": 1, "Name": "rider", "Weight": 1.25, "Vulnerability Profile": "Vulnerable road user on bicycle or scooter."},
                {"Class ID": 2, "Name": "car", "Weight": 1.00, "Vulnerability Profile": "Standard passenger automobile baseline."},
                {"Class ID": 3, "Name": "truck", "Weight": 1.05, "Vulnerability Profile": "Heavy commercial freight vehicle; high inertia."},
                {"Class ID": 4, "Name": "bus", "Weight": 1.05, "Vulnerability Profile": "Public transit vehicle; passenger density."},
                {"Class ID": 5, "Name": "train", "Weight": 1.00, "Vulnerability Profile": "Rail transport crossing vehicle."},
                {"Class ID": 6, "Name": "motorcycle", "Weight": 1.20, "Vulnerability Profile": "High acceleration, low profile, vulnerable rider."},
                {"Class ID": 7, "Name": "bicycle", "Weight": 1.20, "Vulnerability Profile": "Low speed, vulnerable non-motorized cycle."},
                {"Class ID": 8, "Name": "traffic light", "Weight": 0.80, "Vulnerability Profile": "Signaling infrastructure; collision warning lowered."},
                {"Class ID": 9, "Name": "traffic sign", "Weight": 0.80, "Vulnerability Profile": "Regulatory road signage; stationary."},
            ]
            st.dataframe(pd.DataFrame(tax_rows), hide_index=True, width="stretch")

        with col_t2:
            st.markdown("##### Environmental Hazard Multipliers ($M_{\text{cond}}$)")
            cond_rows = [
                {"Condition": "Day (Clear)", "Multiplier": "1.00x", "Driving Physics Justification": "Baseline daylight braking distance and optical clarity."},
                {"Condition": "Unknown / Overcast", "Multiplier": "1.05x", "Driving Physics Justification": "Diffused sky illumination; mild contrast attenuation."},
                {"Condition": "Rain", "Multiplier": "1.15x", "Driving Physics Justification": "Wet asphalt reduces tire traction; braking distance increases +30%."},
                {"Condition": "Night", "Multiplier": "1.20x", "Driving Physics Justification": "Headlight range limitations; human and sensor reaction delay."},
                {"Condition": "Fog", "Multiplier": "1.25x", "Driving Physics Justification": "Severe visual distance limitation; highest multi-vehicle collision risk."},
            ]
            st.dataframe(pd.DataFrame(cond_rows), hide_index=True, width="stretch")

            st.markdown("##### Complete Situational Risk Formula")
            st.code("""
# Per-Object Collision Risk:
Risk_i = (Proximity_i ** 1.3)
       * Class_Weight[class_id]
       * Condition_Multiplier[condition]
       * Confidence_i
       * Persistence_Factor(track_age)

# Frame Aggregate Collision Score:
Frame_Risk = max(Risk_i) + 0.15 * sum(other_risks)

# Operational Alert Tiers:
SAFE:     Score < 0.25
LOW:      0.25 <= Score < 0.50
MEDIUM:   0.50 <= Score < 0.75
HIGH:     0.75 <= Score < 0.88   (Audible / Visual Warning)
CRITICAL: Score >= 0.88          (Autonomous Brake / Steer Alert)
            """, language="python")

    # ══════════════════════════════════════════════════════════════════════════
    # Sub-Tab 6: Repository Structure & Research Stages
    # ══════════════════════════════════════════════════════════════════════════
    with arch_tab6:
        st.markdown("#### Modular Codebase Architecture & 27 Research Notebook Stages")

        col_r1, col_r2 = st.columns([1.1, 1])
        with col_r1:
            st.markdown("##### Production Library Modules (`src/`)")
            st.code("""
src/
├── condition/         # ResNet-18 Multi-Task Classifier (model.py, dataset.py)
├── cyclegan/          # Generator, Discriminator & Loss (model.py, dataset.py)
├── data/              # BDD100K JSONL Streaming Parser & Split Verification
├── depth/             # Depth Anything V2 Monocular Depth & Box Proximity
├── detection/         # Ultralytics YOLO11 Fine-Tuning & Evaluation Suite
├── enhancement/       # Night, Rain, Fog Residual U-Nets & Adaptive Router
├── pipeline/          # End-to-End Unified AdaptiveRoadVisionPipeline Engine
├── risk/              # Rule-Based Situational Collision Risk Engine
└── tracking/          # ByteTrack Kalman Multi-Object Trajectory Association
            """, language="text")

        with col_r2:
            st.markdown("##### 27-Stage Structured Research Pipeline")
            st.markdown("""
            1. **01-05**: Environment verification, BDD100K dataset validation, JSONL streaming, condition labeling, and stratified train/val/test splits.
            2. **06-10**: CycleGAN dataset preparation, adversarial domain training, synthetic fog generation, veil-index quality check, and dataset re-balancing.
            3. **11-13**: 15K sample preprocessing, multi-task ResNet-18 condition training, and evaluation matrices.
            4. **14-17**: Night, Rain, and Fog residual U-Net training, restoration metric evaluation (PSNR, SSIM).
            5. **18-21**: YOLO11n vs YOLO11s detection training, comparative PR curves, and final detector selection (YOLO11s).
            6. **22-25**: Raw vs. Enhanced detection delta benchmarking, ByteTrack tracking evaluation, Depth Anything V2 monocular depth integration, and risk engine calibration.
            7. **26-27**: End-to-end multi-stage pipeline integration, live video streaming verification, and final consolidated benchmark report.
            """)

        st.divider()
        st.markdown("##### Quick Start CLI Execution")
        c_q1, c_q2 = st.columns(2)
        with c_q1:
            st.markdown("**Launch Interactive Streamlit Web App**")
            st.code("streamlit run app.py", language="bash")
        with c_q2:
            st.markdown("**Run CLI Inference on Custom Road Images**")
            st.code("python scripts/run_pipeline.py --input path/to/image.jpg", language="bash")



# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown("""
    <div style="padding:8px 0 20px">
      <h1 style="font-size:2rem;margin-bottom:2px">\U0001f697 Adaptive Road Vision</h1>
      <p style="color:#64748b;font-size:.9rem;margin:0">
        AI-Powered Scene Understanding &nbsp;&middot;&nbsp; Object Detection
        &nbsp;&middot;&nbsp; Real-Time Collision Risk Assessment
      </p>
    </div>""", unsafe_allow_html=True)

    cfg = render_sidebar()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Single Image",
        "Batch Analysis",
        "Real-Time Video",
        "Risk Explorer",
        "About",
    ])
    with tab1: tab_single_image(cfg)
    with tab2: tab_batch(cfg)
    with tab3: tab_video(cfg)
    with tab4: tab_risk_explorer()
    with tab5: tab_about()


if __name__ == "__main__":
    main()
