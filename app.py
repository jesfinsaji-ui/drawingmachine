"""
LineForge — Streamlit Web App  (Login + Signup + ESP32 Direct Send)
Image → Grayscale → Edges → Contours → G-code → ESP32

SETUP:
    pip install streamlit opencv-python-headless numpy pillow requests

Streamlit Secrets required:
    GITHUB_TOKEN = "ghp_..."
    GITHUB_REPO  = "jesfinsaji-ui/drawingmachine"
"""

import math
import datetime
import json
import base64
import hashlib

import requests
import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw


# ══════════════════════════════════════════════
#  GITHUB USER STORE
# ══════════════════════════════════════════════

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO  = st.secrets["GITHUB_REPO"]
USERS_FILE   = "users.json"
API_BASE     = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{USERS_FILE}"
GH_HEADERS   = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_users_with_sha():
    r = requests.get(API_BASE, headers=GH_HEADERS)
    if r.status_code == 404:
        return {}, None
    if r.status_code == 200:
        data    = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return {}, None


def save_users(users: dict, sha) -> bool:
    encoded = base64.b64encode(json.dumps(users, indent=2).encode()).decode()
    payload = {"message": "update users.json", "content": encoded}
    if sha:
        payload["sha"] = sha
    r = requests.put(API_BASE, headers=GH_HEADERS, json=payload)
    return r.status_code in (200, 201)


# ══════════════════════════════════════════════
#  ESP32 COMMUNICATION
# ══════════════════════════════════════════════

def send_gcode_to_esp32(ip: str, gcode: str, port: int = 80, timeout: int = 10):
    url = f"http://{ip}:{port}/gcode"
    try:
        response = requests.post(
            url,
            data=gcode.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=timeout
        )
        if response.status_code == 200:
            return True, response.text.strip() or "G-code sent successfully."
        else:
            return False, f"ESP32 returned HTTP {response.status_code}: {response.text.strip()}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused. Check the IP address and make sure ESP32 is on the same WiFi."
    except requests.exceptions.Timeout:
        return False, f"Connection timed out after {timeout}s. ESP32 may be busy or unreachable."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def ping_esp32(ip: str, port: int = 80, timeout: int = 4):
    try:
        r = requests.get(f"http://{ip}:{port}/ping", timeout=timeout)
        return r.status_code == 200, r.text.strip()
    except:
        return False, "Not reachable"


# ══════════════════════════════════════════════
#  SESSION BOOTSTRAP
# ══════════════════════════════════════════════

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "login"
if "esp32_ip" not in st.session_state:
    st.session_state.esp32_ip = "192.168.1.100"
if "esp32_port" not in st.session_state:
    st.session_state.esp32_port = 80
if "esp32_status" not in st.session_state:
    st.session_state.esp32_status = None


# ══════════════════════════════════════════════
#  SHARED CSS  (used on both auth + main pages)
# ══════════════════════════════════════════════

AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg: #0c0c0c; --card: #181818; --border: #272727;
    --accent: #e8c547; --accent2: #4ecdc4; --red: #e05c5c;
    --green: #7ec893; --text: #e0dfd8; --sub: #555550;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace;
}

[data-testid="collapsedControl"],
[data-testid="stSidebar"] { display: none !important; }

.block-container { padding-top: 0 !important; max-width: 460px !important; }

.auth-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    padding: 48px 40px 8px;
    position: relative;
}

.auth-logo {
    font-family: 'Syne', sans-serif;
    font-size: 26px; font-weight: 800;
    color: var(--text); letter-spacing: -0.02em; margin-bottom: 4px;
}
.auth-logo span { color: var(--accent); }

.auth-sub {
    font-size: 10px; color: var(--sub);
    text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 32px;
}

.corner-mark {
    position: absolute; top: 12px; right: 16px;
    font-size: 10px; color: var(--sub); letter-spacing: 0.08em;
}

.tab-row {
    display: flex; border: 1px solid var(--border);
    border-radius: 2px; overflow: hidden; margin-bottom: 4px;
}

.tab-item {
    flex: 1; text-align: center; padding: 10px;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
}

.tab-active   { background: var(--accent); color: #0c0c0c; }
.tab-inactive { background: #101010; color: var(--sub); }

.stTextInput > div > div > input {
    background-color: #101010 !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important; padding: 12px 14px !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important; outline: none !important;
}

.stTextInput label {
    font-size: 10px !important; font-weight: 700 !important;
    color: var(--sub) !important; text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stButton > button {
    background-color: var(--accent) !important; color: #0c0c0c !important;
    border: none !important; border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important; font-size: 12px !important;
    letter-spacing: 0.1em !important; padding: 14px 20px !important;
    width: 100% !important; margin-top: 6px; transition: opacity 0.15s;
}

.stButton > button:hover { opacity: 0.85 !important; }

[data-testid="stAlert"] {
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
}

.grid-bg {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 40px 40px; opacity: 0.25;
    pointer-events: none; z-index: 0;
}

.divider { height: 1px; background: var(--border); margin: 16px 0; }

.footer-note {
    font-size: 10px; color: var(--sub); text-align: center;
    margin-top: 20px; letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace;
}
</style>
"""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg: #0c0c0c; --panel: #131313; --card: #181818; --border: #272727;
    --accent: #e8c547; --accent2: #4ecdc4; --red: #e05c5c;
    --text: #e0dfd8; --sub: #555550; --gcode: #7ec893;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--panel) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stSidebar"] .stTextInput > div > div > input {
    background-color: #101010 !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    font-size: 12px !important;
    padding: 8px 10px !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 1px var(--accent2) !important;
}

[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stSlider label {
    font-size: 10px !important;
    color: var(--sub) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] .stNumberInput input {
    background-color: #101010 !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    font-size: 12px !important;
}

[data-testid="stSidebar"] .stButton > button {
    background-color: var(--accent) !important;
    color: #0c0c0c !important;
    border: none !important;
    border-radius: 2px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    padding: 8px 12px !important;
    width: 100% !important;
    letter-spacing: 0.08em !important;
}

/* ── Main area buttons ── */
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

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}

.stTextArea textarea, .stNumberInput input {
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stat-box {
    background: var(--card); border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 12px 16px; border-radius: 2px; margin: 4px 0;
}
.stat-box .label { font-size: 10px; color: var(--sub); text-transform: uppercase; letter-spacing: 0.1em; }
.stat-box .value { font-size: 20px; font-weight: 700; color: var(--accent); font-family: 'Syne', sans-serif; }

.panel-header {
    background: #0e0e0e; border: 1px solid var(--border); border-bottom: none;
    padding: 8px 14px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--sub);
    font-family: 'JetBrains Mono', monospace;
}

.title-block {
    display: flex; align-items: baseline; gap: 16px;
    padding: 0 0 24px 0; border-bottom: 1px solid var(--border); margin-bottom: 24px;
}
.title-block h1 { font-size: 32px; margin: 0; padding: 0; }
.title-block .sub { font-size: 12px; color: var(--sub); font-family: 'JetBrains Mono', monospace; }

.gcode-block {
    background: #080808; border: 1px solid var(--border);
    color: var(--gcode); font-family: 'JetBrains Mono', monospace;
    font-size: 11px; padding: 16px; border-radius: 2px;
    max-height: 300px; overflow-y: auto; white-space: pre; line-height: 1.6;
}

div[data-testid="stImage"] img { border: 1px solid var(--border); border-radius: 2px; }

.stNumberInput label, .stSlider label {
    font-size: 11px !important; color: var(--sub) !important;
    text-transform: uppercase; letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace !important;
}

hr { border-color: var(--border) !important; }

[data-testid="stFileUploader"] {
    background: var(--card) !important;
    border: 1px dashed var(--border) !important; border-radius: 2px !important;
}

/* ── ESP32 panel ── */
.esp32-panel {
    background: #0d1a0d; border: 1px solid #1a3a1a;
    border-left: 3px solid var(--accent2);
    border-radius: 2px; padding: 16px; margin: 8px 0;
}

.esp32-send-btn > button {
    background: #0d1a0d !important;
    color: var(--accent2) !important;
    border: 1px solid var(--accent2) !important;
    font-size: 13px !important;
}
</style>
"""


# ══════════════════════════════════════════════
#  AUTH GATE
# ══════════════════════════════════════════════

if not st.session_state.authenticated:

    st.set_page_config(
        page_title="LineForge — Auth",
        page_icon="✏️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown('<div class="grid-bg"></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)

    is_login = st.session_state.page == "login"

    st.markdown(f"""
    <div class="auth-card">
        <div class="corner-mark">v2.0</div>
        <div class="auth-logo">LINE<span>.</span>FORGE</div>
        <div class="auth-sub">Image → Contours → G-code → ESP32</div>
        <div class="tab-row">
            <div class="tab-item {'tab-active' if is_login else 'tab-inactive'}">▸ Login</div>
            <div class="tab-item {'tab-active' if not is_login else 'tab-inactive'}">▸ Sign Up</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── LOGIN ─────────────────────────────────
    if is_login:
        username = st.text_input("Username", placeholder="enter username", key="li_user")
        password = st.text_input("Password", placeholder="••••••••", type="password", key="li_pass")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("→  ACCESS LINEFORGE", key="btn_login"):
            if not username or not password:
                st.error("✗  Please fill in all fields.")
            else:
                with st.spinner("Checking credentials…"):
                    users, _ = get_users_with_sha()
                if username in users and users[username]["password"] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("✗  Invalid username or password.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        if st.button("Don't have an account?  Sign Up →", key="btn_go_signup"):
            st.session_state.page = "signup"
            st.rerun()

    # ── SIGN UP ───────────────────────────────
    else:
        new_user  = st.text_input("Choose a Username", placeholder="e.g. jeswin",       key="su_user")
        new_email = st.text_input("Email",              placeholder="you@example.com",   key="su_email")
        new_pass  = st.text_input("Password",           placeholder="min. 6 characters", type="password", key="su_pass")
        new_pass2 = st.text_input("Confirm Password",   placeholder="repeat password",   type="password", key="su_pass2")

        if new_pass:
            s = len(new_pass)
            color = "#e05c5c" if s < 6 else "#e8c547" if s < 10 else "#7ec893"
            width = "33%"     if s < 6 else "66%"      if s < 10 else "100%"
            label = "Weak"    if s < 6 else "Medium"   if s < 10 else "Strong"
            st.markdown(f"""
            <div style="font-size:10px;color:{color};font-family:'JetBrains Mono',monospace;
                        text-transform:uppercase;letter-spacing:0.1em;margin-top:-6px;">
                Password: {label}
            </div>
            <div style="background:#272727;border-radius:2px;height:3px;margin-bottom:10px;">
                <div style="background:{color};width:{width};height:3px;border-radius:2px;"></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("→  CREATE ACCOUNT", key="btn_signup"):
            if not new_user or not new_email or not new_pass or not new_pass2:
                st.error("✗  Please fill in all fields.")
            elif len(new_user) < 3:
                st.error("✗  Username must be at least 3 characters.")
            elif "@" not in new_email or "." not in new_email:
                st.error("✗  Please enter a valid email address.")
            elif len(new_pass) < 6:
                st.error("✗  Password must be at least 6 characters.")
            elif new_pass != new_pass2:
                st.error("✗  Passwords do not match.")
            else:
                with st.spinner("Creating your account…"):
                    users, sha = get_users_with_sha()
                    if new_user in users:
                        st.error(f"✗  Username '{new_user}' is already taken.")
                    else:
                        users[new_user] = {
                            "password": hash_password(new_pass),
                            "email":    new_email,
                            "created":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        if save_users(users, sha):
                            st.success(f"✓  Account created! Welcome, {new_user}. Please log in.")
                            st.session_state.page = "login"
                            st.rerun()
                        else:
                            st.error("✗  Could not save account. Check your Streamlit secrets.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        if st.button("Already have an account?  Log In →", key="btn_go_login"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown('<div class="footer-note">LINEFORGE · RESTRICTED ACCESS</div>', unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════
#  MAIN APP  (only reaches here after login)
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="LineForge",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(MAIN_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  IMAGE PIPELINE CLASSES
# ══════════════════════════════════════════════

class ImageProcessor:
    @staticmethod
    def to_grayscale(bgr):
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def detect_edges(gray, low=50, high=150):
        return cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), low, high)

    @staticmethod
    def pil_to_bgr(pil_img):
        return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


class ContourEngine:
    def __init__(self, min_points=8):
        self.min_points = max(2, min_points)

    def extract(self, edge_image):
        raw, _ = cv2.findContours(edge_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        return [
            [(int(p[0][0]), int(p[0][1])) for p in cnt]
            for cnt in raw if len(cnt) >= self.min_points
        ]

    @staticmethod
    def sort_nearest_neighbour(contours):
        if not contours:
            return contours
        remaining = list(contours)
        ordered   = [remaining.pop(0)]
        while remaining:
            last_pt = ordered[-1][-1]
            idx = min(range(len(remaining)),
                      key=lambda i: math.hypot(remaining[i][0][0] - last_pt[0],
                                               remaining[i][0][1] - last_pt[1]))
            ordered.append(remaining.pop(idx))
        return ordered


class Scaler:
    def __init__(self, board_w, board_h, margin=5.0):
        self.board_w = board_w; self.board_h = board_h; self.margin = margin
        self.draw_w  = board_w - 2 * margin
        self.draw_h  = board_h - 2 * margin
        if self.draw_w <= 0 or self.draw_h <= 0:
            raise ValueError("Margin too large.")

    def scale(self, contours, image_shape):
        ih, iw = image_shape[:2]
        k  = min(self.draw_w / iw, self.draw_h / ih)
        ox = self.margin + (self.draw_w - iw * k) / 2
        oy = self.margin + (self.draw_h - ih * k) / 2
        return [
            [(round(px*k+ox, 3), round((ih-py)*k+oy, 3)) for px, py in cnt]
            for cnt in contours if len(cnt) >= 2
        ]


class GCodeGenerator:
    def __init__(self, feed_rate=1500, z_up=3.0, z_down=0.0):
        self.feed_rate = feed_rate; self.z_up = z_up; self.z_down = z_down

    def generate(self, contours, board_w, board_h):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"; LineForge   : {ts}",
            f"; Board       : {board_w} x {board_h} mm",
            f"; Feed rate   : {self.feed_rate} mm/min",
            f"; Contours    : {len(contours)}",
            f"; Total pts   : {sum(len(c) for c in contours)}",
            "G21 G90", f"G0 Z{self.z_up:.2f}", "G0 X0.000 Y0.000", "",
        ]
        for i, cnt in enumerate(contours):
            x0, y0 = cnt[0]
            lines += [
                f"; Contour {i+1}/{len(contours)} ({len(cnt)} pts)",
                f"G0 Z{self.z_up:.2f}", f"G0 X{x0:.3f} Y{y0:.3f}",
                f"G1 Z{self.z_down:.2f} F{self.feed_rate}",
            ]
            for x, y in cnt[1:]:
                lines.append(f"G1 X{x:.3f} Y{y:.3f}")
            lines += [f"G0 Z{self.z_up:.2f}", ""]
        lines += [f"G0 Z{self.z_up:.2f}", "G0 X0.000 Y0.000", "M2"]
        return "\n".join(lines)


class ToolpathRenderer:
    BG = "#0a0a0a"; STROKE = "#4ecdc4"; TRAVEL = "#2a2a2a"
    START_DOT = "#e05c5c"; BOARD_LINE = "#3a3a3a"; GRID = "#161616"

    def __init__(self, w=700, h=520):
        self.w = w; self.h = h

    def render(self, contours, board_w, board_h):
        img  = Image.new("RGB", (self.w, self.h), self.BG)
        draw = ImageDraw.Draw(img)
        pad  = 32
        scale = min((self.w-2*pad)/board_w, (self.h-2*pad)/board_h)
        ox = pad + ((self.w-2*pad) - board_w*scale) / 2
        oy = pad + ((self.h-2*pad) - board_h*scale) / 2

        def mm2px(x, y):
            return (int(ox + x*scale), int(oy + (board_h - y)*scale))

        for gx in range(10, int(board_w), 10):
            p = int(ox + gx*scale)
            draw.line([(p, int(oy)), (p, int(oy + board_h*scale))], fill=self.GRID)
        for gy in range(10, int(board_h), 10):
            p = int(oy + (board_h - gy)*scale)
            draw.line([(int(ox), p), (int(ox + board_w*scale), p)], fill=self.GRID)

        bx0, by0 = mm2px(0, 0); bx1, by1 = mm2px(board_w, board_h)
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
        if length < 1: return
        dx, dy = (x1-x0)/length, (y1-y0)/length
        t, on = 0, True
        while t < length:
            t2 = min(t+dash, length)
            if on:
                draw.line([(int(x0+dx*t), int(y0+dy*t)),
                            (int(x0+dx*t2), int(y0+dy*t2))], fill=color)
            t += dash; on = not on


def run_pipeline(pil_img, board_w, board_h, margin,
                 feed_rate, z_up, z_down, canny_low, canny_high, min_points):
    bgr      = ImageProcessor.pil_to_bgr(pil_img)
    gray     = ImageProcessor.to_grayscale(bgr)
    edges    = ImageProcessor.detect_edges(gray, canny_low, canny_high)
    engine   = ContourEngine(min_points=min_points)
    contours = ContourEngine.sort_nearest_neighbour(engine.extract(edges))
    scaled   = Scaler(board_w, board_h, margin).scale(contours, bgr.shape)
    gcode    = GCodeGenerator(feed_rate, z_up, z_down).generate(scaled, board_w, board_h)
    preview  = ToolpathRenderer(700, 520).render(scaled, board_w, board_h)
    return scaled, gcode, preview, edges


# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════

with st.sidebar:

    # User badge
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#555550;
                padding:8px 0 14px 0;border-bottom:1px solid #272727;margin-bottom:12px;">
        <span style="color:#4ecdc4;font-weight:700;">●</span>
        LOGGED IN AS
        <span style="color:#e8c547;font-weight:700;margin-left:4px;">
            {st.session_state.username.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── ESP32 Connection ──────────────────────
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#4ecdc4;text-transform:uppercase;
                letter-spacing:0.15em;padding:4px 0 6px 0;border-bottom:1px solid #272727;
                margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
        ▸ ESP32 Connection
    </div>
    """, unsafe_allow_html=True)

    esp_ip = st.text_input(
        "ESP32 IP Address",
        value=st.session_state.esp32_ip,
        placeholder="192.168.1.100",
        key="esp_ip_input"
    )

    esp_port = st.number_input(
        "Port", min_value=1, max_value=65535,
        value=st.session_state.esp32_port, step=1
    )

    # Connection status badge
    status = st.session_state.esp32_status
    if status == "online":
        st.markdown("""
        <div style="font-size:11px;color:#7ec893;font-family:'JetBrains Mono',monospace;
                    padding:6px 0;font-weight:700;">
            ● ONLINE — ESP32 reachable
        </div>""", unsafe_allow_html=True)
    elif status == "offline":
        st.markdown("""
        <div style="font-size:11px;color:#e05c5c;font-family:'JetBrains Mono',monospace;
                    padding:6px 0;font-weight:700;">
            ● OFFLINE — Cannot reach ESP32
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:11px;color:#555550;font-family:'JetBrains Mono',monospace;
                    padding:6px 0;">
            ● NOT CHECKED
        </div>""", unsafe_allow_html=True)

    if st.button("⬡  PING ESP32", key="btn_ping"):
        st.session_state.esp32_ip   = esp_ip
        st.session_state.esp32_port = int(esp_port)
        with st.spinner("Pinging…"):
            ok, msg = ping_esp32(esp_ip, int(esp_port))
        st.session_state.esp32_status = "online" if ok else "offline"
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Board ─────────────────────────────────
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#e8c547;text-transform:uppercase;
                letter-spacing:0.15em;padding:4px 0 6px 0;border-bottom:1px solid #272727;
                margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
        ▸ Board (mm)
    </div>
    """, unsafe_allow_html=True)

    board_w = st.number_input("Width",  min_value=10, max_value=2000, value=200, step=10)
    board_h = st.number_input("Height", min_value=10, max_value=2000, value=150, step=10)
    margin  = st.number_input("Margin", min_value=0,  max_value=50,   value=5,   step=1)

    # ── Motion ────────────────────────────────
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#e8c547;text-transform:uppercase;
                letter-spacing:0.15em;padding:4px 0 6px 0;border-bottom:1px solid #272727;
                margin-top:12px;margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
        ▸ Motion
    </div>
    """, unsafe_allow_html=True)

    feed_rate = st.number_input("Feed Rate (mm/min)", min_value=100, max_value=10000, value=1500, step=100)
    z_up      = st.number_input("Z Pen-Up (mm)",   min_value=0.0,  max_value=20.0, value=3.0, step=0.5)
    z_down    = st.number_input("Z Pen-Down (mm)", min_value=-5.0, max_value=5.0,  value=0.0, step=0.5)

    # ── Edge Detection ────────────────────────
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#e8c547;text-transform:uppercase;
                letter-spacing:0.15em;padding:4px 0 6px 0;border-bottom:1px solid #272727;
                margin-top:12px;margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
        ▸ Edge Detection
    </div>
    """, unsafe_allow_html=True)

    canny_low  = st.slider("Canny Low",  0, 255, 50)
    canny_high = st.slider("Canny High", 0, 255, 150)
    min_points = st.slider("Min Points", 2, 50,   8)

    st.markdown("---")

    if st.button("⏻  LOGOUT"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.page = "login"
        st.rerun()

    st.markdown(
        '<p style="font-size:10px;color:#555550;font-family:JetBrains Mono,monospace;margin-top:8px;">'
        'LINEFORGE v2.0<br>Image → Contours → G-code → ESP32</p>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════

st.markdown("""
<div class="title-block">
    <h1>LINEFORGE</h1>
    <span class="sub">Image → Grayscale → Edges → Contours → G-code → ESP32</span>
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
        st.markdown('<div class="panel-header"><span style="color:#e8c547">●</span> Original Image</div>', unsafe_allow_html=True)
        st.image(pil_img, use_container_width=True)
    with col_info:
        st.markdown('<div class="panel-header"><span style="color:#e8c547">●</span> File Info</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-box">
            <div class="label">Filename</div>
            <div class="value" style="font-size:13px;">{uploaded.name}</div>
        </div>
        <div class="stat-box">
            <div class="label">Dimensions</div>
            <div class="value">{w}x{h}</div>
        </div>
        <div class="stat-box">
            <div class="label">Board</div>
            <div class="value" style="font-size:14px;">{board_w}x{board_h}mm</div>
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
                st.session_state["last_gcode"]   = gcode
                st.session_state["last_preview"] = preview
                st.session_state["last_edges"]   = edges
                st.session_state["last_scaled"]  = scaled
            except Exception as ex:
                st.error(f"Pipeline error: {ex}")

    # ── Results ───────────────────────────────
    if "last_gcode" in st.session_state:
        gcode   = st.session_state["last_gcode"]
        preview = st.session_state["last_preview"]
        edges   = st.session_state["last_edges"]
        scaled  = st.session_state["last_scaled"]

        n_contours  = len(scaled)
        n_points    = sum(len(c) for c in scaled)
        gcode_lines = gcode.count("\n") + 1

        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "Contours",     str(n_contours)),
            (c2, "Total Points", str(n_points)),
            (c3, "G-code Lines", str(gcode_lines)),
            (c4, "Board (mm)",   f"{board_w}x{board_h}"),
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
            st.image(cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB), use_container_width=True)

        with col_gc:
            st.markdown('<div class="panel-header"><span style="color:#7ec893">●</span> G-code Output</div>', unsafe_allow_html=True)
            preview_lines = "\n".join(gcode.split("\n")[:120])
            if gcode_lines > 120:
                preview_lines += f"\n\n; ... ({gcode_lines - 120} more lines) ..."
            st.markdown(f'<div class="gcode-block">{preview_lines}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Download
            st.download_button(
                label="💾  Download G-code",
                data=gcode,
                file_name=f"lineforge_{uploaded.name.rsplit('.',1)[0]}.gcode",
                mime="text/plain",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Send to ESP32 ─────────────────
            st.markdown('<div class="panel-header"><span style="color:#4ecdc4">●</span> Send to ESP32</div>', unsafe_allow_html=True)

            cur_ip   = st.session_state.esp32_ip
            cur_port = st.session_state.esp32_port
            cur_status = st.session_state.esp32_status

            status_color = "#7ec893" if cur_status == "online" else "#e05c5c" if cur_status == "offline" else "#555550"
            status_text  = "ONLINE" if cur_status == "online" else "OFFLINE" if cur_status == "offline" else "NOT CHECKED"

            st.markdown(f"""
            <div class="esp32-panel">
                <div style="font-size:10px;color:#4ecdc4;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.15em;margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
                    ▸ HARDWARE TARGET
                </div>
                <div style="font-size:12px;color:#e0dfd8;margin-bottom:6px;font-family:'JetBrains Mono',monospace;">
                    IP: <span style="color:#e8c547;">{cur_ip}</span>
                    &nbsp;&nbsp;Port: <span style="color:#e8c547;">{cur_port}</span>
                </div>
                <div style="font-size:11px;color:#555550;margin-bottom:8px;font-family:'JetBrains Mono',monospace;">
                    {n_contours} contours · {n_points} points · {gcode_lines} lines
                </div>
                <div style="font-size:11px;font-weight:700;color:{status_color};font-family:'JetBrains Mono',monospace;">
                    ● {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='esp32-send-btn'>", unsafe_allow_html=True)
            send_clicked = st.button("⬡  SEND TO ESP32 — START DRAWING", key="btn_send_esp32")
            st.markdown("</div>", unsafe_allow_html=True)

            if send_clicked:
                with st.spinner(f"Sending {gcode_lines} lines to {cur_ip}:{cur_port}…"):
                    ok, msg = send_gcode_to_esp32(cur_ip, gcode, int(cur_port))
                if ok:
                    st.success(f"✓  ESP32 acknowledged: {msg}")
                else:
                    st.error(f"✗  {msg}")
                    st.markdown("""
                    <div style="font-size:11px;color:#555550;font-family:'JetBrains Mono',monospace;
                                padding:10px;background:#100a0a;border:1px solid #2a1a1a;
                                border-radius:2px;margin-top:8px;">
                        Troubleshooting:<br>
                        · Make sure ESP32 and your computer are on the same WiFi<br>
                        · Verify the IP address in the sidebar matches Serial Monitor<br>
                        · Use PING button first to confirm connection<br>
                        · Confirm esp32_lineforge.ino is flashed on the device
                    </div>
                    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="border:1px dashed #272727;border-radius:2px;padding:80px 40px;
                text-align:center;margin-top:24px;background:#101010;">
        <div style="font-size:48px;margin-bottom:16px;">⬡</div>
        <div style="font-family:Syne,sans-serif;font-size:20px;color:#e0dfd8;margin-bottom:8px;">
            Upload an image to begin
        </div>
        <div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#555550;">
            Supports PNG · JPG · BMP · TIFF
        </div>
    </div>
    """, unsafe_allow_html=True)
