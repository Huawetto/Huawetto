#!/usr/bin/env python3
"""
camera_full_gui.py
Local offline camera GUI with dropdown menus, deform controls, control-points, image effects.
Dependencies: PyQt5, OpenCV (opencv-python), numpy, Pillow (optional for saving metadata)
Run: python camera_full_gui.py
"""

import sys
import os
import json
import math
import time
from functools import partial
from datetime import datetime

import numpy as np
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets

# ---------- Defaults ----------
DEFAULT_MIN_ZOOM = -150.0
DEFAULT_MAX_ZOOM = 50.0
DEFAULT_ZOOM_BASE = 1.001
PREVIEW_W = 1280
PREVIEW_H = 720
FPS = 30

# ---------- Utility functions ----------
def bgr_to_qimage(frame_bgr):
    """Convert opencv BGR image to QImage"""
    if frame_bgr is None:
        return QtGui.QImage()
    # ensure contiguous
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    return QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888).copy()


def apply_color_effects(img_bgr, brightness=0.0, contrast=1.0, saturation=1.0, gamma=1.0, tint=(0,0,0,0)):
    """
    brightness: -1..1 added (after scaling)
    contrast: 0..3 multiplier (1.0 default)
    saturation: 0..3 multiplier (1.0 default)
    gamma: >0 (1 default)
    tint: tuple (b,g,r,alpha) alpha 0..1 to blend
    """
    if img_bgr is None:
        return None
    img = img_bgr.astype(np.float32) / 255.0

    # contrast + brightness (simple)
    img = (img - 0.5) * contrast + 0.5 + brightness

    # saturation: move toward luminance for desaturation / away for oversaturation
    # luminance for BGR channels (B,G,R)
    lum = img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299
    img = img * saturation + lum[..., None] * (1.0 - saturation)

    # gamma correction
    img = np.clip(img, 0.0, 1.0)
    if gamma != 1.0 and gamma > 0.0:
        img = np.power(img, 1.0 / gamma)

    # tint blending
    try:
        tb, tg, tr, ta = tint
        ta = float(ta)
    except Exception:
        tb = tg = tr = 0
        ta = 0.0
    if ta > 0.0:
        tint_color = np.array([tb, tg, tr], dtype=np.float32) / 255.0
        img = img * (1.0 - ta) + tint_color[None, None, :] * ta

    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    return img


# ---------- Deformation map builders ----------
def build_base_mesh(w, h):
    """Return normalized meshgrid coordinates in range [0..1]"""
    xs = np.linspace(0, 1, w, dtype=np.float32)
    ys = np.linspace(0, 1, h, dtype=np.float32)
    xv, yv = np.meshgrid(xs, ys)
    return xv, yv


def compute_zoom_factor(zoom_base, deform_value):
    # safe exponent (avoid overflow). If zoom_base == 1.0 then ln==0 and zoom_factor==1
    zoom_base_safe = max(1e-6, float(zoom_base))
    try:
        ln = math.log(zoom_base_safe)
    except Exception:
        ln = 0.0
    exp = np.clip(deform_value * ln, -50.0, 50.0)
    return float(math.exp(exp))


def build_remap(w, h, zoom_factor=1.0, distortion=0.0, edge_power=2.0, mirror_x=1.0, control_points=None):
    """
    Build map_x, map_y (float32 pixel coordinates) for cv2.remap
    - zoom_factor: >0. If >1 -> zoom-in. If <1 -> zoom-out
    - distortion: barrel coefficient (positive barrel, negative pincushion)
    - edge_power: how quickly effect decays toward edges (>1 more centered)
    - control_points: list of dicts {x, y, strength, radius}
    """
    xv, yv = build_base_mesh(w, h)
    cx, cy = 0.5, 0.5
    # vector from center normalized [-0.5..0.5]
    vx = xv - cx
    vy = yv - cy
    r = np.sqrt(vx*vx + vy*vy)  # 0..~0.707
    # normalize r to 0..1 (0 center, 1 corner)
    rmax = math.sqrt(0.5*0.5 + 0.5*0.5)
    rn = r / rmax
    # local zoom decays toward edges: local = lerp(zoom_factor, 1.0, (rn^edge_power))
    with np.errstate(invalid='ignore'):
        tpow = np.power(np.clip(rn, 0.0, 1.0), max(0.0001, edge_power))
    local_zoom = zoom_factor * (1.0 - tpow) + 1.0 * tpow  # center = zoom_factor, edge ~1.0
    # apply local zoom (centered sample)
    x_zoomed = cx + vx / np.maximum(local_zoom, 1e-6)
    y_zoomed = cy + vy / np.maximum(local_zoom, 1e-6)

    # apply global barrel distortion on zoomed coords (using radius from center after zoom)
    dx = x_zoomed - cx
    dy = y_zoomed - cy
    rr = np.sqrt(dx*dx + dy*dy)
    # polynomial distortion
    k = float(distortion)
    radial = 1.0 + k * (rr*rr)  # + 0.0*(rr**4) - reserved
    x_dist = cx + dx * radial
    y_dist = cy + dy * radial

    # apply control points displacement additive (gaussian based)
    if control_points:
        disp_x = np.zeros_like(x_dist)
        disp_y = np.zeros_like(y_dist)
        for pt in control_points:
            px = float(pt.get('x', 0.5))
            py = float(pt.get('y', 0.5))
            strength = float(pt.get('strength', 0.0))
            radius = float(pt.get('radius', 0.2))
            dxp = x_dist - px
            dyp = y_dist - py
            dr = np.sqrt(dxp*dxp + dyp*dyp)
            sigma = max(1e-6, radius)
            influence = np.exp(- (dr*dr) / (2.0 * (sigma*sigma)))
            with np.errstate(divide='ignore', invalid='ignore'):
                dirx = np.where(dr>0, dxp / dr, 0.0)
                diry = np.where(dr>0, dyp / dr, 0.0)
            mag = strength * influence
            disp_x += dirx * mag
            disp_y += diry * mag
        x_dist = x_dist + disp_x
        y_dist = y_dist + disp_y

    # mirror if requested
    if mirror_x < 0:
        x_dist = 1.0 - x_dist

    # clamp sampling coords to [0..1] and convert to pixel space
    x_clamped = np.clip(x_dist, 0.0, 1.0) * (w - 1)
    y_clamped = np.clip(y_dist, 0.0, 1.0) * (h - 1)

    return x_clamped.astype(np.float32), y_clamped.astype(np.float32)


# ---------- Main Qt Application ----------
class CameraWindow(QtWidgets.QMainWindow):
    def __init__(self, cam_index=0):
        super().__init__()
        self.setWindowTitle("Camera Studio — By Huawetto with AI")
        self.cam_index = cam_index

        # state
        self.preview_w = PREVIEW_W
        self.preview_h = PREVIEW_H
        self.min_zoom = DEFAULT_MIN_ZOOM
        self.max_zoom = DEFAULT_MAX_ZOOM
        self.zoom_base = DEFAULT_ZOOM_BASE

        self.deform_value = 0.0
        self.edge_power = 2.2
        self.distortion = 0.0
        self.zoom_factor = 1.0
        self.control_points = []  # list of dicts
        self.mirror_x = 1.0

        # color/effects params
        self.brightness = 0.0
        self.contrast = 1.0
        self.saturation = 1.0
        self.gamma = 1.0
        self.tint = (0,0,0,0)

        # remap cache
        self.cached_params = None
        self.map_x = None
        self.map_y = None

        # last frames for capture
        self.last_frame = None
        self.last_display = None
        self.is_paused = False

        # Build UI
        self._build_ui()

        # Open camera (use CAP_DSHOW on Windows to avoid long grab delays)
        if sys.platform.startswith("win"):
            self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        else:
            # most platforms will accept a single integer index
            self.cap = cv2.VideoCapture(self.cam_index)
        # set desired size (may be ignored by some cameras/drivers)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.preview_w))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.preview_h))

        # Timer for update
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / FPS))

    def _build_ui(self):
        # Central widget: horizontal split
        central = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(central)
        self.setCentralWidget(central)

        # Left: controls
        left = QtWidgets.QFrame()
        left.setFixedWidth(420)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(12,12,12,12)
        left_layout.setSpacing(8)

        # Deform group
        grp_deform = QtWidgets.QGroupBox("Deformazione / Zoom")
        gdl = QtWidgets.QFormLayout()
        self.dropdown_deform = QtWidgets.QComboBox()
        self.dropdown_deform.addItems(["Radial (barrel/pincushion)", "Fisheye-ish", "Bulge/Pinch via points", "Custom: mix"])
        gdl.addRow("Type:", self.dropdown_deform)

        self.spin_deform = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.spin_deform.setMinimum(int(self.min_zoom))
        self.spin_deform.setMaximum(int(self.max_zoom))
        self.spin_deform.setValue(0)
        self.spin_deform.valueChanged.connect(self.on_deform_slider)
        gdl.addRow("Deform value:", self.spin_deform)

        self.lbl_deform_val = QtWidgets.QLabel("0")
        gdl.addRow("Current:", self.lbl_deform_val)

        self.sld_edge = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_edge.setRange(1, 500)
        self.sld_edge.setValue(int(self.edge_power*10))
        self.sld_edge.valueChanged.connect(self.on_edge_changed)
        gdl.addRow("EdgePower:", self.sld_edge)

        self.sld_dist = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_dist.setRange(-200, 200)
        self.sld_dist.setValue(int(self.distortion*100))
        self.sld_dist.valueChanged.connect(self.on_dist_changed)
        gdl.addRow("Distortion (k):", self.sld_dist)

        grp_deform.setLayout(gdl)
        left_layout.addWidget(grp_deform)

        # Control points group
        grp_pts = QtWidgets.QGroupBox("Punti di deformazione (click preview per aggiungere)")
        vpts = QtWidgets.QVBoxLayout()
        self.list_pts = QtWidgets.QListWidget()
        vpts.addWidget(self.list_pts)
        btns_pt = QtWidgets.QHBoxLayout()
        self.btn_remove_pt = QtWidgets.QPushButton("Rimuovi selezionato")
        self.btn_remove_pt.clicked.connect(self.remove_selected_point)
        btns_pt.addWidget(self.btn_remove_pt)
        self.btn_clear_pts = QtWidgets.QPushButton("Pulisci tutti")
        self.btn_clear_pts.clicked.connect(self.clear_points)
        btns_pt.addWidget(self.btn_clear_pts)
        vpts.addLayout(btns_pt)
        grp_pts.setLayout(vpts)
        left_layout.addWidget(grp_pts)

        # Color / image effects
        grp_color = QtWidgets.QGroupBox("Colori & Effetti")
        gcol = QtWidgets.QFormLayout()
        self.sld_brightness = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_brightness.setRange(-100,100)
        self.sld_brightness.setValue(0)
        self.sld_brightness.valueChanged.connect(self.on_brightness)
        gcol.addRow("Brightness:", self.sld_brightness)

        self.sld_contrast = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_contrast.setRange(10,300)
        self.sld_contrast.setValue(100)
        self.sld_contrast.valueChanged.connect(self.on_contrast)
        gcol.addRow("Contrast%:", self.sld_contrast)

        self.sld_saturation = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_saturation.setRange(0,300)
        self.sld_saturation.setValue(100)
        self.sld_saturation.valueChanged.connect(self.on_saturation)
        gcol.addRow("Saturation%:", self.sld_saturation)

        self.sld_gamma = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_gamma.setRange(10,500)
        self.sld_gamma.setValue(100)
        self.sld_gamma.valueChanged.connect(self.on_gamma)
        gcol.addRow("Gamma%:", self.sld_gamma)

        grp_color.setLayout(gcol)
        left_layout.addWidget(grp_color)

        # Save/load presets
        grp_presets = QtWidgets.QGroupBox("Presets / Profile")
        gp = QtWidgets.QHBoxLayout()
        self.btn_save_profile = QtWidgets.QPushButton("Salva profilo")
        self.btn_save_profile.clicked.connect(self.save_profile)
        self.btn_load_profile = QtWidgets.QPushButton("Carica profilo")
        self.btn_load_profile.clicked.connect(self.load_profile)
        gp.addWidget(self.btn_save_profile)
        gp.addWidget(self.btn_load_profile)
        grp_presets.setLayout(gp)
        left_layout.addWidget(grp_presets)

        left_layout.addStretch(1)

        # Right: preview + capture
        right = QtWidgets.QFrame()
        rlayout = QtWidgets.QVBoxLayout(right)
        rlayout.setContentsMargins(4,4,4,4)
        # preview label
        self.lbl_preview = QtWidgets.QLabel()
        self.lbl_preview.setFixedSize(self.preview_w, self.preview_h)
        self.lbl_preview.setStyleSheet("background-color: black;")
        self.lbl_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_preview.mousePressEvent = self.on_preview_click
        rlayout.addWidget(self.lbl_preview, alignment=QtCore.Qt.AlignCenter)

        # bottom center capture button
        btn_bar = QtWidgets.QWidget()
        bar_layout = QtWidgets.QHBoxLayout(btn_bar)
        bar_layout.addStretch(1)
        self.btn_capture = QtWidgets.QPushButton("Scatta")
        # style: blue text, green bg, black border
        self.btn_capture.setStyleSheet("color: blue; background-color: green; border: 2px solid black; font-weight: bold; font-size: 18px; padding: 12px 24px;")
        self.btn_capture.clicked.connect(self.on_capture)
        bar_layout.addWidget(self.btn_capture)
        bar_layout.addStretch(1)
        rlayout.addWidget(btn_bar)

        # compose main layout
        hbox.addWidget(left)
        hbox.addWidget(right)

        # status bar
        self.status = QtWidgets.QLabel("Ready")
        self.statusBar().addWidget(self.status, 1)

    # ---------- Slots / UI handlers ----------
    def on_deform_slider(self, val):
        self.deform_value = float(val)
        self.lbl_deform_val.setText(f"{self.deform_value:.1f}")
        self.invalidate_map()

    def on_edge_changed(self, val):
        self.edge_power = max(0.1, val / 10.0)
        self.invalidate_map()

    def on_dist_changed(self, val):
        self.distortion = float(val) / 100.0
        self.invalidate_map()

    def on_brightness(self, val):
        self.brightness = float(val) / 100.0

    def on_contrast(self, val):
        self.contrast = float(val) / 100.0

    def on_saturation(self, val):
        self.saturation = float(val) / 100.0

    def on_gamma(self, val):
        self.gamma = float(val) / 100.0

    def invalidate_map(self):
        self.cached_params = None

    def remove_selected_point(self):
        for item in self.list_pts.selectedItems():
            row = self.list_pts.row(item)
            if 0 <= row < len(self.control_points):
                del self.control_points[row]
                self.list_pts.takeItem(row)
        self.invalidate_map()

    def clear_points(self):
        self.control_points.clear()
        self.list_pts.clear()
        self.invalidate_map()

    def on_preview_click(self, ev):
        # add a control point at normalized coordinates of click (relative to label size)
        pos = ev.pos()
        w = self.lbl_preview.width()
        h = self.lbl_preview.height()
        if w == 0 or h == 0:
            return
        # map pos to normalized [0..1]
        nx = pos.x() / float(w)
        ny = pos.y() / float(h)
        # default strength and radius
        pt = {"x": nx, "y": ny, "strength": 0.06, "radius": 0.12}
        self.control_points.append(pt)
        self.list_pts.addItem(f"pt {len(self.control_points)}: ({nx:.2f},{ny:.2f}) s={pt['strength']:.3f} r={pt['radius']:.2f}")
        self.invalidate_map()

    def save_profile(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save profile", "", "JSON files (*.json)")
        if not fname:
            return
        data = {
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "zoom_base": self.zoom_base,
            "deform_value": self.deform_value,
            "edge_power": self.edge_power,
            "distortion": self.distortion,
            "control_points": self.control_points,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "gamma": self.gamma,
        }
        try:
            with open(fname, "w") as f:
                json.dump(data, f, indent=2)
            self.status.setText(f"Saved profile {os.path.basename(fname)}")
        except Exception as e:
            self.status.setText(f"Error saving profile: {e}")

    def load_profile(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load profile", "", "JSON files (*.json)")
        if not fname:
            return
        try:
            with open(fname, "r") as f:
                data = json.load(f)
        except Exception as e:
            self.status.setText(f"Error loading profile: {e}")
            return
        self.min_zoom = data.get("min_zoom", self.min_zoom)
        self.max_zoom = data.get("max_zoom", self.max_zoom)
        self.zoom_base = data.get("zoom_base", self.zoom_base)
        self.deform_value = data.get("deform_value", self.deform_value)
        self.edge_power = data.get("edge_power", self.edge_power)
        self.distortion = data.get("distortion", self.distortion)
        self.control_points = data.get("control_points", self.control_points)
        self.brightness = data.get("brightness", self.brightness)
        self.contrast = data.get("contrast", self.contrast)
        self.saturation = data.get("saturation", self.saturation)
        self.gamma = data.get("gamma", self.gamma)
        # update UI sliders
        try:
            self.spin_deform.setMinimum(int(self.min_zoom))
            self.spin_deform.setMaximum(int(self.max_zoom))
            self.spin_deform.setValue(int(self.deform_value))
            self.sld_edge.setValue(int(self.edge_power * 10))
            self.sld_dist.setValue(int(self.distortion * 100))
            self.sld_brightness.setValue(int(self.brightness * 100))
            self.sld_contrast.setValue(int(self.contrast * 100))
            self.sld_saturation.setValue(int(self.saturation * 100))
            self.sld_gamma.setValue(int(self.gamma * 100))
        except Exception:
            pass
        self.list_pts.clear()
        for i,pt in enumerate(self.control_points):
            try:
                self.list_pts.addItem(f"pt {i+1}: ({pt['x']:.2f},{pt['y']:.2f}) s={pt['strength']:.3f} r={pt['radius']:.2f}")
            except Exception:
                self.list_pts.addItem(f"pt {i+1}: (invalid data)")
        self.invalidate_map()
        self.status.setText(f"Loaded profile {os.path.basename(fname)}")

    # ---------- Helper: scale & crop ----------
    def _fit_frame(self, frame, target_w, target_h):
        """Scale and center-crop the frame to exactly target_w x target_h (keeps aspect ratio)."""
        if frame is None:
            return np.zeros((target_h, target_w, 3), dtype=np.uint8)
        h, w = frame.shape[:2]
        if w == 0 or h == 0:
            return np.zeros((target_h, target_w, 3), dtype=np.uint8)
        src_aspect = w / h
        dst_aspect = target_w / target_h
        # scale to cover (like CSS cover)
        if src_aspect > dst_aspect:
            # source wider -> fit height, crop width
            scale = target_h / h
            new_w = int(w * scale)
            resized = cv2.resize(frame, (new_w, target_h), interpolation=cv2.INTER_LINEAR)
            x0 = (new_w - target_w) // 2
            cropped = resized[:, x0:x0+target_w]
        else:
            # source taller -> fit width, crop height
            scale = target_w / w
            new_h = int(h * scale)
            resized = cv2.resize(frame, (target_w, new_h), interpolation=cv2.INTER_LINEAR)
            y0 = (new_h - target_h) // 2
            cropped = resized[y0:y0+target_h, :]
        return cropped

    # ---------- Main loop ----------
    def _tick(self):
        if self.is_paused:
            return
        frame_bgr = None
        if not self.cap or not self.cap.isOpened():
            # no camera: show placeholder
            placeholder = np.zeros((self.preview_h, self.preview_w, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera not available", (50, self.preview_h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
            frame_bgr = placeholder
        else:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # show placeholder if read fails
                    placeholder = np.zeros((self.preview_h, self.preview_w, 3), dtype=np.uint8)
                    cv2.putText(placeholder, "Camera read failed", (50, self.preview_h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
                    frame_bgr = placeholder
                else:
                    frame_bgr = self._fit_frame(frame, self.preview_w, self.preview_h)
            except Exception:
                placeholder = np.zeros((self.preview_h, self.preview_w, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Camera error", (50, self.preview_h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
                frame_bgr = placeholder

        # store last raw frame
        self.last_frame = None if frame_bgr is None else frame_bgr.copy()

        # compute maps if needed
        ctrl_tuple = tuple((p.get('x',0.5), p.get('y',0.5), p.get('strength',0.0), p.get('radius',0.2)) for p in self.control_points)
        params = (self.preview_w, self.preview_h, float(self.deform_value), float(self.zoom_base), float(self.distortion), float(self.edge_power), ctrl_tuple, float(self.mirror_x))
        if self.cached_params != params:
            # rebuild remap
            zoom_factor = compute_zoom_factor(self.zoom_base, self.deform_value)
            ctrl = []
            for p in self.control_points:
                ctrl.append({'x': p.get('x', 0.5), 'y': p.get('y', 0.5), 'strength': p.get('strength', 0.0), 'radius': p.get('radius', 0.2)})
            try:
                self.map_x, self.map_y = build_remap(self.preview_w, self.preview_h, zoom_factor, self.distortion, self.edge_power, self.mirror_x, control_points=ctrl)
            except Exception:
                self.map_x, self.map_y = None, None
            self.cached_params = params

        # remap the frame
        if (self.map_x is not None) and (self.map_y is not None) and (self.last_frame is not None):
            try:
                warped = cv2.remap(self.last_frame, self.map_x, self.map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            except Exception:
                warped = self.last_frame.copy()
        else:
            warped = None if self.last_frame is None else self.last_frame.copy()

        # color effects
        eff = apply_color_effects(warped, brightness=self.brightness, contrast=self.contrast, saturation=self.saturation, gamma=self.gamma, tint=self.tint)
        self.last_display = None if eff is None else eff.copy()

        # display
        qim = bgr_to_qimage(eff) if eff is not None else QtGui.QImage()
        if not qim.isNull():
            pix = QtGui.QPixmap.fromImage(qim).scaled(self.lbl_preview.width(), self.lbl_preview.height(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.lbl_preview.setPixmap(pix)
        else:
            self.lbl_preview.clear()

    # ---------- Capture ----------
    def on_capture(self):
        """Save the last displayed image to disk (timestamped)"""
        if self.last_display is None:
            self.status.setText("No frame to capture")
            return
        folder = os.path.expanduser("~/Pictures")
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            folder = os.getcwd()
        fname = datetime.now().strftime("capture_%Y%m%d_%H%M%S.png")
        path = os.path.join(folder, fname)
        try:
            # last_display is BGR
            cv2.imwrite(path, self.last_display)
            self.status.setText(f"Saved capture: {path}")
        except Exception as e:
            self.status.setText(f"Error saving image: {e}")

    # ---------- Cleanup ----------
    def closeEvent(self, ev):
        try:
            if hasattr(self, "timer") and self.timer is not None:
                self.timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "cap") and self.cap is not None and self.cap.isOpened():
                try:
                    self.cap.release()
                except Exception:
                    pass
        except Exception:
            pass
        super().closeEvent(ev)


# ---------- Run ----------
def main():
    app = QtWidgets.QApplication(sys.argv)
    # optional: allow passing camera index as argument
    cam_index = 0
    if len(sys.argv) > 1:
        try:
            cam_index = int(sys.argv[1])
        except Exception:
            cam_index = 0
    w = CameraWindow(cam_index=cam_index)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
