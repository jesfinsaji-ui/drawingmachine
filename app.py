"""
DRAWING MACHINE — Streamlit Web App  (with Login)
Image → Grayscale → Edges → Contours → G-code → Preview

SETUP:
    pip install streamlit opencv-python-headless numpy pillow

RUN:
    streamlit run app.py
"""

import math
import datetime
import io

import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw


# ══════════════════════════════════════════════
#  LOGIN SYSTEM
# ══════════════════════════════════════════════

# ── Credentials — edit these ─────────────────
USERS = {
    "admin": "machine2024",
    "user1": "drawbot",
}

# ── Session bootstrap ─────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ── Login gate ────────────────────────────────
if not st.session_state.authenticated:

    st.set_page_config(
        page_title="Drawing Machine — Login",
        page_icon="✏️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

    :root {
        --bg: #0c0c0c;
        --panel: #131313;
        --card: #181818;
        --border: #272727;
        --accent: #e8c547;
        --accent2: #4ecdc4;
        --red: #e05c5c;
        --text: #e0dfd8;
        --sub: #555550;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace;
    }

    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"]        { display: none !important; }

    .block-container {
        padding-top: 0 !important;
        max-width: 460px !important;
    }

    .login-card {
        width: 100%;
        background: var(--card);
        border: 1px solid var(--border);
        border-top: 3px solid var(--accent);
        padding: 48px 40px 40px;
        margin-bottom: 0;
        position: relative;
    }

    .login-logo {
        font-family: 'Syne', sans-serif;
        font-size: 28px;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.02em;
        margin-bottom: 4px;
    }

    .login-logo span { color: var(--accent); }

    .login-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: var(--sub);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 40px;
    }

    .stTextInput > div > div > input {
        background-color: #101010 !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        padding: 12px 14px !important;
        transition: border-color 0.15s;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
        outline: none !important;
    }

    .stTextInput label {
        font-size: 10px !important;
        font-weight: 700 !important;
        color: var(--sub) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stButton > button {
        background-color: var(--accent) !important;
        color: #0c0c0c !important;
        border: none !important;
        border-radius: 2px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        letter-spacing: 0.1em !important;
        padding: 14px 20px !important;
        width: 100% !important;
        margin-top: 8px;
        transition: opacity 0.15s;
        text-transform: uppercase;
    }

    .stButton > button:hover { opacity: 0.85 !important; }

    [data-testid="stAlert"] {
        background-color: #1a0a0a !important;
        border: 1px solid var(--red) !important;
        border-radius: 2px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
    }

    .corner-mark {
        position: absolute;
        top: 12px;
        right: 16px;
        font-size: 10px;
        color: var(--sub);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.08em;
    }

    .grid-bg {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            linear-gradient(var(--border) 1px, transparent 1px),
            linear-gradient(90deg, var(--border) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
    }

    .footer-note {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: var(--sub);
        text-align: center;
        margin-top: 20px;
        letter-spacing: 0.08em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="grid-bg"></div>', unsafe_allow_html=True)

    # Vertical spacer to centre card
    st.markdown("<div style='height: 12vh'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="login-card">
        <div class="corner-mark">v2.0</div>
        <div class="login-logo">DRAWING<span>.</span>MACHINE</div>
        <div class="login-sub">Image → Contours → G-code</div>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="enter username", key="login_user")
    password = st.text_input("Password", placeholder="••••••••", type="password", key="login_pass")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("→  ACCESS MACHINE"):
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("✗  Invalid credentials. Check username and password.")

    st.markdown("""
    <div class="footer-note">DRAWING MACHINE · RESTRICTED ACCESS</div>
    """, unsafe_allow_html=True)

    st.stop()   # Nothing below renders until authenticated


# ══════════════════════════════════════════════
#  PAGE CONFIG  (runs only after login)
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="Drawing Machine",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════
#  CUSTOM CSS
# ══════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg: #0c0c0c;
    --panel: #131313;
    --card: #181818;
    --border: #272727;
    --accent: #e8c547;
    --accent2: #4ecdc4;
    --red: #e05c5c;
    --text: #e0dfd8;
    --sub: #555550;
    --gcode: #7ec893;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace;
}

[data-testid="stSidebar"] {
    background-color: var(--panel) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
    letter-spacing: -0.02em;
}

.stButton > button {
    background-color: var(--accent) !important;
    color: #0c0c0c !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    width: 100%;
    transition: opacity 0.15s;
}

.stButton > button:hover { opacity: 0.85; }

.stDownloadButton > button {
    background-color: #1a2a1a !important;
    color: var(--accent2) !important;
    border: 1px solid var(--accent2) !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    width: 100%;
}

.stTextArea textarea, .stNumberInput input, .stSlider {
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stat-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 12px 16px;
    border-radius: 2px;
    margin: 4px 0;
}

.stat-box .label {
    font-size: 10px;
    color: var(--sub);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
}

.stat-box .value {
    font-size: 20px;
    font-weight: 700;
    color: var(--accent);
    font-family: 'Syne', sans-serif;
}

.panel-header {
    background: #0e0e0e;
    border: 1px solid var(--border);
    border-bottom: none;
    padding: 8px 14px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--sub);
    font-family: 'JetBrains Mono', monospace;
}

.panel-header span { color: var(--accent); }

.section-label {
    font-size: 10px;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-family: 'JetBrains Mono', monospace;
    padding: 12px 0 4px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
}

.gcode-block {
    background: #080808;
    border: 1px solid var(--border);
    color: var(--gcode);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 16px;
    border-radius: 2px;
    max-height: 420px;
    overflow-y: auto;
    white-space: pre;
    line-height: 1.6;
}

.title-block {
    display: flex;
    align-items: baseline;
    gap: 16px;
    padding: 0 0 24px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}

.title-block h1 {
    font-size: 32px;
    margin: 0;
    padding: 0;
    color: var(--text) !important;
}

.title-block .sub {
    font-size: 12px;
    color: var(--sub);
    font-family: 'JetBrains Mono', monospace;
}

div[data-testid="stImage"] img {
    border: 1px solid var(--border);
    border-radius: 2px;
}

.stNumberInput label, .stSlider label, .stSelectbox label {
    font-size: 11px !important;
    color: var(--sub) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace !important;
}

hr {
    border-color: var(--border) !important;
}

[data-testid="stFileUploader"] {
    background: var(--card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 2px !important;
}

.user-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--sub);
    display: flex;
    align-items: center;
    gap: 6px;
}

.user-badge span {
    color: var(--accent2);
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  1 — IMAGE PROCESSOR
# ══════════════════════════════════════════════

class ImageProcessor:
    @staticmethod
    def to_grayscale(bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def detect_edges(gray: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return cv2.Canny(blurred, low, high)

    @staticmethod
    def pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
        return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

    @staticmethod
    def bgr_to_pil(bgr: np.ndarray) -> Image.Image:
        return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


# ══════════════════════════════════════════════
#  2 — CONTOUR ENGINE
# ══════════════════════════════════════════════

class ContourEngine:
    def __init__(self, min_points: int = 8):
        self.min_points = max(2, min_points)

    def extract(self, edge_image: np.ndarray) -> list:
        raw, _ = cv2.findContours(edge_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        result = []
        for cnt in raw:
            pts = [(int(p[0][0]), int(p[0][1])) for p in cnt]
            if len(pts) >= self.min_points:
                result.append(pts)
        return result

    @staticmethod
    def sort_nearest_neighbour(contours: list) -> list:
        if not contours:
            return contours
        remaining = list(contours)
        ordered   = [remaining.pop(0)]
        while remaining:
            last_pt = ordered[-1][-1]
            closest_idx = min(
                range(len(remaining)),
                key=lambda i: math.hypot(remaining[i][0][0] - last_pt[0],
                                          remaining[i][0][1] - last_pt[1])
            )
            ordered.append(remaining.pop(closest_idx))
        return ordered


# ══════════════════════════════════════════════
#  3 — SCALER
# ══════════════════════════════════════════════

class Scaler:
    def __init__(self, board_w: float, board_h: float, margin: float = 5.0):
        self.board_w = board_w
        self.board_h = board_h
        self.margin  = margin
        self.draw_w  = board_w - 2 * margin
        self.draw_h  = board_h - 2 * margin
        if self.draw_w <= 0 or self.draw_h <= 0:
            raise ValueError("Margin too large for board size.")

    def scale(self, contours: list, image_shape: tuple) -> list:
        ih, iw = image_shape[:2]
        k      = min(self.draw_w / iw, self.draw_h / ih)
        off_x  = self.margin + (self.draw_w - iw * k) / 2
        off_y  = self.margin + (self.draw_h - ih * k) / 2
        scaled = []
        for cnt in contours:
            pts = []
            for px, py in cnt:
                x_mm = round(px * k + off_x, 3)
                y_mm = round((ih - py) * k + off_y, 3)
                pts.append((x_mm, y_mm))
            if len(pts) >= 2:
                scaled.append(pts)
        return scaled


# ══════════════════════════════════════════════
#  4 — G-CODE GENERATOR
# ══════════════════════════════════════════════

class GCodeGenerator:
    def __init__(self, feed_rate: int = 1500, z_up: float = 3.0, z_down: float = 0.0):
        self.feed_rate = feed_rate
        self.z_up      = z_up
        self.z_down    = z_down

    def generate(self, contours: list, board_w: float, board_h: float) -> str:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"; Generated   : {ts}",
            f"; Board       : {board_w} × {board_h} mm",
            f"; Feed rate   : {self.feed_rate} mm/min",
            f"; Contours    : {len(contours)}",
            f"; Total pts   : {sum(len(c) for c in contours)}",
            "G21 G90",
            f"G0 Z{self.z_up:.2f}",
            "G0 X0.000 Y0.000",
            "",
        ]
        for i, cnt in enumerate(contours):
            x0, y0 = cnt[0]
            lines += [
                f"; Contour {i+1}/{len(contours)} ({len(cnt)} pts)",
                f"G0 Z{self.z_up:.2f}",
                f"G0 X{x0:.3f} Y{y0:.3f}",
                f"G1 Z{self.z_down:.2f} F{self.feed_rate}",
            ]
            for x, y in cnt[1:]:
                lines.append(f"G1 X{x:.3f} Y{y:.3f}")
            lines.append(f"G0 Z{self.z_up:.2f}")
            lines.append("")
        lines += [f"G0 Z{self.z_up:.2f}", "G0 X0.000 Y0.000", "M2"]
        return "\n".join(lines)


# ══════════════════════════════════════════════
#  5 — TOOLPATH RENDERER
# ══════════════════════════════════════════════

class ToolpathRenderer:
    BG         = "#0a0a0a"
    STROKE     = "#4ecdc4"
    TRAVEL     = "#2a2a2a"
    START_DOT  = "#e05c5c"
    BOARD_LINE = "#3a3a3a"
    GRID       = "#161616"

    def __init__(self, w: int = 700, h: int = 520):
        self.w = w
        self.h = h

    def render(self, contours: list, board_w: float, board_h: float) -> Image.Image:
        img  = Image.new("RGB", (self.w, self.h), self.BG)
        draw = ImageDraw.Draw(img)

        pad   = 32
        scale = min((self.w - 2*pad) / board_w, (self.h - 2*pad) / board_h)
        ox    = pad + ((self.w - 2*pad) - board_w * scale) / 2
        oy    = pad + ((self.h - 2*pad) - board_h * scale) / 2

        def mm2px(x, y):
            return (int(ox + x * scale), int(oy + (board_h - y) * scale))

        for gx in range(10, int(board_w), 10):
            p = int(ox + gx * scale)
            draw.line([(p, int(oy)), (p, int(oy + board_h * scale))], fill=self.GRID)
        for gy in range(10, int(board_h), 10):
            p = int(oy + (board_h - gy) * scale)
            draw.line([(int(ox), p), (int(ox + board_w * scale), p)], fill=self.GRID)

        bx0, by0 = mm2px(0, 0)
        bx1, by1 = mm2px(board_w, board_h)
        draw.rectangle([bx0, by1, bx1, by0], outline=self.BOARD_LINE, width=2)

        prev = None
        for cnt in contours:
            sp = mm2px(*cnt[0])
            if prev:
                self._dashed(draw, prev, sp, self.TRAVEL)
            prev = mm2px(*cnt[-1])

        for cnt in contours:
            pts = [mm2px(x, y) for x, y in cnt]
            if len(pts) >= 2:
                draw.line(pts, fill=self.STROKE, width=1)
            sx, sy = pts[0]
            draw.ellipse([sx-3, sy-3, sx+3, sy+3], fill=self.START_DOT)

        return img

    def _dashed(self, draw, p0, p1, color, dash=6):
        x0, y0 = p0; x1, y1 = p1
        length = math.hypot(x1-x0, y1-y0)
        if length < 1:
            return
        dx, dy = (x1-x0)/length, (y1-y0)/length
        t, on = 0, True
        while t < length:
            t2 = min(t + dash, length)
            if on:
                draw.line([(int(x0+dx*t), int(y0+dy*t)),
                            (int(x0+dx*t2), int(y0+dy*t2))], fill=color)
            t += dash; on = not on


# ══════════════════════════════════════════════
#  PIPELINE
# ══════════════════════════════════════════════

def run_pipeline(pil_img, board_w, board_h, margin,
                 feed_rate, z_up, z_down,
                 canny_low, canny_high, min_points):
    bgr      = ImageProcessor.pil_to_bgr(pil_img)
    gray     = ImageProcessor.to_grayscale(bgr)
    edges    = ImageProcessor.detect_edges(gray, canny_low, canny_high)

    engine   = ContourEngine(min_points=min_points)
    contours = engine.extract(edges)
    contours = ContourEngine.sort_nearest_neighbour(contours)

    scaler   = Scaler(board_w, board_h, margin)
    scaled   = scaler.scale(contours, bgr.shape)

    gen      = GCodeGenerator(feed_rate, z_up, z_down)
    gcode    = gen.generate(scaled, board_w, board_h)

    renderer = ToolpathRenderer(700, 520)
    preview  = renderer.render(scaled, board_w, board_h)

    return scaled, gcode, preview, edges


# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════

with st.sidebar:
    # User badge at top of sidebar
    st.markdown(f"""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #555550;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid #272727;
        margin-bottom: 8px;
        display: flex;
        gap: 8px;
        align-items: center;
    ">
        <span style="color:#4ecdc4; font-weight:700;">●</span>
        LOGGED IN AS <span style="color:#e8c547; font-weight:700; margin-left:4px;">{st.session_state.username.upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">▸ Board (mm)</div>', unsafe_allow_html=True)
    board_w = st.number_input("Width",   min_value=10, max_value=2000, value=200, step=10)
    board_h = st.number_input("Height",  min_value=10, max_value=2000, value=150, step=10)
    margin  = st.number_input("Margin",  min_value=0,  max_value=50,   value=5,   step=1)

    st.markdown('<div class="section-label">▸ Motion</div>', unsafe_allow_html=True)
    feed_rate = st.number_input("Feed Rate (mm/min)", min_value=100, max_value=10000, value=1500, step=100)
    z_up      = st.number_input("Z Pen-Up (mm)",   min_value=0.0, max_value=20.0, value=3.0, step=0.5)
    z_down    = st.number_input("Z Pen-Down (mm)", min_value=-5.0, max_value=5.0, value=0.0, step=0.5)

    st.markdown('<div class="section-label">▸ Edge Detection</div>', unsafe_allow_html=True)
    canny_low  = st.slider("Canny Low",    0, 255, 50)
    canny_high = st.slider("Canny High",   0, 255, 150)
    min_points = st.slider("Min Points",   2, 50,  8)

    st.markdown("---")

    # Logout button
    if st.button("⏻  LOGOUT"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.markdown(
        '<p style="font-size:10px;color:#555550;font-family:JetBrains Mono,monospace;">'
        'DRAWING MACHINE v2.0<br>Image → Contours → G-code</p>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

st.markdown("""
<div class="title-block">
    <h1>DRAWING MACHINE</h1>
    <span class="sub">Image → Grayscale → Edges → Contours → G-code</span>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop an image here or click to browse",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    label_visibility="visible"
)

if uploaded:
    pil_img = Image.open(uploaded).convert("RGB")
    w, h    = pil_img.size

    col_orig, col_info = st.columns([3, 1])
    with col_orig:
        st.markdown('<div class="panel-header"><span>●</span> Original Image</div>', unsafe_allow_html=True)
        st.image(pil_img, use_container_width=True)
    with col_info:
        st.markdown('<div class="panel-header"><span>●</span> File Info</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Filename</div>
            <div class="value" style="font-size:13px;">{uploaded.name}</div>
        </div>
        <div class="stat-box">
            <div class="label">Dimensions</div>
            <div class="value">{w}×{h}</div>
        </div>
        <div class="stat-box">
            <div class="label">Board</div>
            <div class="value" style="font-size:14px;">{board_w}×{board_h}mm</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⚙  PROCESS IMAGE"):
        with st.spinner("Running pipeline…"):
            try:
                scaled, gcode, preview, edges = run_pipeline(
                    pil_img, float(board_w), float(board_h), float(margin),
                    int(feed_rate), float(z_up), float(z_down),
                    int(canny_low), int(canny_high), int(min_points)
                )

                n_contours  = len(scaled)
                n_points    = sum(len(c) for c in scaled)
                gcode_lines = gcode.count("\n") + 1

                c1, c2, c3, c4 = st.columns(4)
                for col, label, val in [
                    (c1, "Contours",    str(n_contours)),
                    (c2, "Total Points",str(n_points)),
                    (c3, "G-code Lines",str(gcode_lines)),
                    (c4, "Board (mm)",  f"{board_w}×{board_h}"),
                ]:
                    col.markdown(f"""
                    <div class="stat-box">
                        <div class="label">{label}</div>
                        <div class="value">{val}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                col_tp, col_gc = st.columns([1, 1])

                with col_tp:
                    st.markdown('<div class="panel-header"><span style="color:#4ecdc4">●</span> Toolpath Preview</div>', unsafe_allow_html=True)
                    st.image(preview, use_container_width=True)

                    st.markdown('<div class="panel-header" style="margin-top:16px"><span style="color:#e8c547">●</span> Edge Detection</div>', unsafe_allow_html=True)
                    edge_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
                    st.image(edge_rgb, use_container_width=True)

                with col_gc:
                    st.markdown('<div class="panel-header"><span style="color:#7ec893">●</span> G-code Output</div>', unsafe_allow_html=True)
                    preview_lines = "\n".join(gcode.split("\n")[:120])
                    if gcode_lines > 120:
                        preview_lines += f"\n\n; ... ({gcode_lines - 120} more lines) ..."
                    st.markdown(f'<div class="gcode-block">{preview_lines}</div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button(
                        label="💾  Download G-code",
                        data=gcode,
                        file_name=f"drawing_{uploaded.name.rsplit('.',1)[0]}.gcode",
                        mime="text/plain",
                    )

            except Exception as ex:
                st.error(f"Pipeline error: {ex}")

else:
    st.markdown("""
    <div style="
        border: 1px dashed #272727;
        border-radius: 2px;
        padding: 80px 40px;
        text-align: center;
        margin-top: 24px;
        background: #101010;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">⬡</div>
        <div style="font-family: Syne, sans-serif; font-size: 20px; color: #e0dfd8; margin-bottom: 8px;">
            Upload an image to begin
        </div>
        <div style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #555550;">
            Supports PNG · JPG · BMP · TIFF
        </div>
    </div>
    """, unsafe_allow_html=True)
