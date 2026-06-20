#!/usr/bin/env python3
"""
SONOS RAY イコライザー制御 - Qt GUI 拡張版
SONOS RAY Equalizer Controller - Extended Qt GUI

インストール / Installation:
  pip install PyQt6 soco pynput

実行 / Run:
  python sonos_eq_gui_advanced.py
"""

import sys
import os
import threading
from typing import Optional, List

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QComboBox, QCheckBox, QGroupBox,
    QStatusBar, QMessageBox, QScrollArea, QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QSpinBox, QLineEdit, QSizePolicy,
    QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QIcon, QFont, QImage, QPixmap, QPainter, QColor, QPainterPath, QCursor
from PyQt6.QtCore import pyqtSignal, QThread, QSize
from soco import SoCo, discover

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), 'src'))

import strings as _strings_mod
from strings import tr, set_language, _DATA_DIR, APP_SETTINGS_PATH
from models import EQPreset, load_presets, save_presets, DEVICE_CACHE_PATH
from controller import SonosEQController


class PresetDialog(QDialog):
    """プリセット作成・編集ダイアログ / Preset create & edit dialog"""

    def __init__(self, parent=None, preset: Optional[EQPreset] = None):
        super().__init__(parent)
        self.preset = preset
        self.init_ui()
        self.setWindowTitle(tr('preset_dialog_title'))
        self.setGeometry(200, 200, 400, 250)

    def init_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        if self.preset:
            self.name_input.setText(self.preset.name)
        layout.addRow(tr('preset_name_label'), self.name_input)

        self.bass_spinbox = QSpinBox()
        self.bass_spinbox.setRange(-10, 10)
        if self.preset:
            self.bass_spinbox.setValue(self.preset.bass)
        layout.addRow(tr('preset_bass_label'), self.bass_spinbox)

        self.treble_spinbox = QSpinBox()
        self.treble_spinbox.setRange(-10, 10)
        if self.preset:
            self.treble_spinbox.setValue(self.preset.treble)
        layout.addRow(tr('preset_treble_label'), self.treble_spinbox)

        self.loudness_checkbox = QCheckBox(tr('enable_checkbox'))
        if self.preset:
            self.loudness_checkbox.setChecked(self.preset.loudness)
        layout.addRow(tr('preset_loudness_label'), self.loudness_checkbox)

        self.speech_checkbox = QCheckBox(tr('enable_checkbox'))
        if self.preset:
            self.speech_checkbox.setChecked(self.preset.speech_enhancement)
        layout.addRow(tr('preset_speech_label'), self.speech_checkbox)

        self.night_checkbox = QCheckBox(tr('enable_checkbox'))
        if self.preset:
            self.night_checkbox.setChecked(self.preset.night_mode)
        layout.addRow(tr('preset_night_label'), self.night_checkbox)

        button_layout = QHBoxLayout()
        ok_button = QPushButton(tr('ok_btn'))
        cancel_button = QPushButton(tr('cancel_btn'))
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def get_preset(self) -> EQPreset:
        return EQPreset(
            name=self.name_input.text(),
            bass=self.bass_spinbox.value(),
            treble=self.treble_spinbox.value(),
            loudness=self.loudness_checkbox.isChecked(),
            speech_enhancement=self.speech_checkbox.isChecked(),
            night_mode=self.night_checkbox.isChecked(),
        )


class SettingsDialog(QDialog):
    """設定ダイアログ — デバイス状態・更新・リセット・言語・バージョン情報
    Settings dialog — Device Status / Refresh / Reset / Language / About"""

    def __init__(self, main_window: 'SonosEQGUIAdvanced'):
        super().__init__(main_window)
        self._main = main_window
        self.setWindowTitle(tr('settings_title'))
        self.setGeometry(150, 150, 420, 580)
        self._init_ui()
        self._refresh_device_status()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Device Status
        status_group = QGroupBox(tr('settings_device_status_group'))
        status_layout = QVBoxLayout()
        self._device_name_label = QLabel(tr('settings_device_name_default'))
        self._device_ip_label = QLabel(tr('settings_ip_default'))
        self._connection_status_label = QLabel(
            tr('settings_status_disconnected'))
        self._status_light_checkbox = QCheckBox(tr('status_light'))
        self._status_light_checkbox.toggled.connect(
            self._on_status_light_changed)
        status_layout.addWidget(self._device_name_label)
        status_layout.addWidget(self._device_ip_label)
        status_layout.addWidget(self._connection_status_label)
        status_layout.addWidget(self._status_light_checkbox)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # EQ Controls
        eq_group = QGroupBox(tr('settings_eq_group'))
        eq_layout = QHBoxLayout()
        refresh_btn = QPushButton(tr('settings_refresh_btn'))
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self._on_refresh)
        reset_btn = QPushButton(tr('settings_reset_btn'))
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self._main.reset_eq_settings)
        eq_layout.addWidget(refresh_btn)
        eq_layout.addWidget(reset_btn)
        eq_group.setLayout(eq_layout)
        layout.addWidget(eq_group)

        # Language
        lang_group = QGroupBox(tr('settings_lang_group'))
        lang_layout = QHBoxLayout()
        en_btn = QPushButton('English')
        ja_btn = QPushButton('日本語')
        en_btn.setMinimumHeight(36)
        ja_btn.setMinimumHeight(36)
        en_btn.setCheckable(True)
        ja_btn.setCheckable(True)
        en_btn.setChecked(_strings_mod._LANG == 'en')
        ja_btn.setChecked(_strings_mod._LANG == 'ja')

        def _switch_en():
            set_language('en')
            en_btn.setChecked(True)
            ja_btn.setChecked(False)
            self._main.retranslate_ui()

        def _switch_ja():
            set_language('ja')
            ja_btn.setChecked(True)
            en_btn.setChecked(False)
            self._main.retranslate_ui()

        en_btn.clicked.connect(_switch_en)
        ja_btn.clicked.connect(_switch_ja)
        lang_layout.addWidget(en_btn)
        lang_layout.addWidget(ja_btn)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        # About
        about_group = QGroupBox(tr('settings_about_group'))
        about_layout = QVBoxLayout()
        about_label = QLabel(tr('about_text'))
        about_label.setWordWrap(True)
        about_layout.addWidget(about_label)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)

        layout.addStretch()

        close_btn = QPushButton(tr('settings_close_btn'))
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _refresh_device_status(self):
        ctrl = self._main.controller
        if ctrl is None:
            self._connection_status_label.setText(
                tr('settings_status_disconnected'))
            self._connection_status_label.setStyleSheet("color: #f44336;")
            return
        try:
            settings = ctrl.get_all_eq_settings()
            self._device_name_label.setText(
                tr('settings_device_name', name=settings['device_name']))
            self._device_ip_label.setText(
                tr('settings_ip', ip=settings['ip_address']))
            self._connection_status_label.setText(
                tr('settings_status_connected'))
            self._connection_status_label.setStyleSheet("color: #4CAF50;")
            if settings.get('status_light') is not None:
                self._status_light_checkbox.blockSignals(True)
                self._status_light_checkbox.setChecked(
                    settings['status_light'])
                self._status_light_checkbox.blockSignals(False)
            self._status_light_checkbox.setEnabled(
                settings.get('status_light') is not None)
        except Exception as e:
            self._connection_status_label.setText(
                tr('settings_status_error', e=e))
            self._connection_status_label.setStyleSheet("color: #f44336;")

    def _on_status_light_changed(self, checked: bool):
        ctrl = self._main.controller
        if ctrl is None:
            return
        try:
            ctrl.set_status_light(checked)
            state = tr('state_on') if checked else tr('state_off')
            self._main.status_bar.showMessage(
                tr('status_setting_status_light', state=state))
        except Exception as e:
            self._main.status_bar.showMessage(f"Error: {e}")

    def _on_refresh(self):
        self._main.refresh_eq_settings()
        self._refresh_device_status()


class VolumeHUD(QWidget):
    """macOSスタイルの音量オーバーレイ表示 / macOS-style volume overlay HUD"""

    _HIDE_DELAY_MS = 1500

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(200, 82)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(0)

        self._icon = QLabel("🔊")
        self._icon.setFont(QFont("Apple Color Emoji", 22))
        top.addWidget(self._icon)

        top.addStretch()

        self._level = QLabel("50")
        self._level.setFont(QFont("SF Pro Display", 20, QFont.Weight.Bold))
        self._level.setStyleSheet("color: white;")
        self._level.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self._level)

        layout.addLayout(top)

        self._bar = QWidget()
        self._bar.setFixedHeight(4)
        self._bar_fill = QWidget(self._bar)
        self._bar_fill.setFixedHeight(4)
        self._bar_fill.setStyleSheet("background: white; border-radius: 2px;")
        self._bar.setStyleSheet(
            "background: rgba(255,255,255,0.30); border-radius: 2px;")
        layout.addWidget(self._bar)

        self.setLayout(layout)

    def show_volume(self, volume: int):
        self._level.setText(str(volume))

        if volume == 0:
            self._icon.setText("🔇")
        elif volume < 34:
            self._icon.setText("🔈")
        elif volume < 67:
            self._icon.setText("🔉")
        else:
            self._icon.setText("🔊")

        # バー幅を音量に合わせてリサイズ（バー全体幅が確定してから）
        # Resize bar fill after the bar's full width is finalized
        def _update_bar():
            w = self._bar.width()
            self._bar_fill.setFixedWidth(max(0, int(w * volume / 100)))

        QTimer.singleShot(0, _update_bar)

        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + screen.height() * 11//12

        self.show()
        self.move(x, y)
        self.raise_()
        self._timer.start(self._HIDE_DELAY_MS)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)
        painter.fillPath(path, QColor(28, 28, 28, 220))
        # painter.setBrush(Qt.BrushStyle.NoBrush)
        # painter.fillPath(path, painter.brush())


class SonosEQGUIAdvanced(QMainWindow):
    """SONOS RAY イコライザー制御 Qt GUI 拡張版 / SONOS RAY EQ Controller — extended Qt GUI"""

    _settings_ready = pyqtSignal(dict)
    _media_key_pressed = pyqtSignal(str)
    _track_info_ready = pyqtSignal(dict)
    _album_art_ready = pyqtSignal(QImage)
    _discover_status = pyqtSignal(str)   # スキャン進捗メッセージ → ステータスバー / scan progress → status bar
    _discover_done = pyqtSignal(list)    # スキャン完了 → デバイスリスト（空=未検出）/ scan done → device list (empty = none found)
    _discover_error = pyqtSignal(str)    # スキャン失敗 / scan error

    def __init__(self):
        super().__init__()
        self.controller: Optional[SonosEQController] = None
        self.presets: List[EQPreset] = load_presets()
        self.update_in_progress = False
        self._keyboard_listener = None
        self._current_uri = ''
        self._pre_mute_volume: Optional[int] = None
        self.selected_preset_index: Optional[int] = None
        self._repeat_mode: str = 'off'
        self._volume_hud = VolumeHUD()

        self._settings_ready.connect(self._apply_settings)
        self._media_key_pressed.connect(self._handle_media_key)
        self._track_info_ready.connect(self._apply_track_info)
        self._album_art_ready.connect(self._apply_album_art)
        self.init_ui()
        self._discover_status.connect(self._on_discover_status)
        self._discover_done.connect(self._on_discover_done)
        self._discover_error.connect(self._on_discover_error)
        self.setWindowTitle(tr('window_title'))
        self.setGeometry(100, 100, 700, 900)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        if not self.load_device_cache():
            self.discover_devices()

        self._start_keyboard_listener()

        self._track_timer = QTimer(self)
        self._track_timer.timeout.connect(self._refresh_track_info)
        self._track_timer.start(5000)

    def init_ui(self):
        """UIを初期化 / Initialize the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        self._scroll_area = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._init_device_section(layout)
        self._init_now_playing_section(layout)
        self._init_playback_section(layout)
        self._init_volume_section(layout)
        self._init_bass_section(layout)
        self._init_treble_section(layout)
        self._init_loudness_section(layout)
        self._init_audio_options_section(layout)
        self._init_presets_section(layout)

        self._settings_button = QPushButton(tr('settings_btn'))
        self._settings_button.clicked.connect(self.open_settings_dialog)
        self._settings_button.setMinimumHeight(36)
        layout.addWidget(self._settings_button)

        layout.addStretch()
        content.setLayout(layout)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        central_widget.setLayout(outer_layout)

        self._init_status_bar()

    def _init_device_section(self, layout: QVBoxLayout):
        device_layout = QHBoxLayout()
        self._device_label = QLabel(tr('device_label'))
        self._device_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.device_combo = QComboBox()
        self.device_combo.addItem(tr('discovering'))
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)

        self.scan_button = QPushButton(tr('scan_btn'))
        self.scan_button.clicked.connect(self.discover_devices)
        self.scan_button.setMinimumHeight(30)

        self.connect_button = QPushButton(tr('connect_btn'))
        self.connect_button.clicked.connect(self.on_device_selected)
        self.connect_button.setMinimumHeight(30)

        device_layout.addWidget(self._device_label)
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.scan_button)
        device_layout.addWidget(self.connect_button)
        layout.addLayout(device_layout)

    def _init_now_playing_section(self, layout: QVBoxLayout):
        self._now_playing_group = QGroupBox(tr('now_playing_group'))
        now_playing_group = self._now_playing_group
        now_playing_layout = QVBoxLayout()
        now_playing_layout.setContentsMargins(8, 8, 8, 8)
        now_playing_layout.setSpacing(6)

        self.album_art_label = QLabel(tr('no_image'))
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.album_art_label.setMinimumHeight(50)
        self._album_art_pixmap: Optional[QPixmap] = None

        self.track_title_label = QLabel("--")
        self.track_title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.track_title_label.setWordWrap(True)
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.track_artist_album_label = QLabel("--")
        self.track_artist_album_label.setWordWrap(True)
        self.track_artist_album_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        now_playing_layout.addWidget(self.album_art_label)
        now_playing_layout.addWidget(self.track_title_label)
        now_playing_layout.addWidget(self.track_artist_album_label)
        now_playing_group.setLayout(now_playing_layout)
        layout.addWidget(now_playing_group)

    def _init_playback_section(self, layout: QVBoxLayout):
        self._playback_group = QGroupBox(tr('playback_group'))
        playback_group = self._playback_group
        playback_layout = QHBoxLayout()
        playback_layout.setSpacing(4)

        self.prev_button = QPushButton("⏮")
        self.play_pause_button = QPushButton("▶")
        self.next_button = QPushButton("⏭")
        self.shuffle_button = QPushButton(tr('shuffle'))
        self.shuffle_button.setCheckable(True)
        self.repeat_button = QPushButton(tr('repeat_off'))
        self.mute_button = QPushButton("🔇")
        self.vol_minus_button = QPushButton("🔉")
        self.vol_plus_button = QPushButton("🔊")

        for btn in (self.prev_button, self.play_pause_button, self.next_button,
                    self.shuffle_button, self.repeat_button,
                    self.mute_button, self.vol_minus_button, self.vol_plus_button):
            btn.setMinimumHeight(44)
            btn.setFont(QFont("Arial", 16))
            playback_layout.addWidget(btn)

        self.prev_button.clicked.connect(self._on_prev_clicked)
        self.play_pause_button.clicked.connect(self._on_play_pause_clicked)
        self.next_button.clicked.connect(self._on_next_clicked)
        self.shuffle_button.clicked.connect(self._on_shuffle_clicked)
        self.repeat_button.clicked.connect(self._on_repeat_clicked)
        self.mute_button.clicked.connect(self._on_mute_clicked)
        self.vol_minus_button.clicked.connect(
            lambda: self.adjust_slider(self.volume_slider, -6, self.on_volume_changed))
        self.vol_plus_button.clicked.connect(
            lambda: self.adjust_slider(self.volume_slider, 6, self.on_volume_changed))

        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)

    def _init_bass_section(self, layout: QVBoxLayout):
        self.bass_group = QGroupBox(tr('bass_group'))
        bass_layout = QVBoxLayout()
        bass_label_layout = QHBoxLayout()
        self._bass_level_label = QLabel(tr('bass_level'))
        bass_label_layout.addWidget(self._bass_level_label)
        self.bass_value_label = QLabel("0")
        self.bass_value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.bass_value_label.setStyleSheet("color: #667eea;")
        bass_label_layout.addWidget(self.bass_value_label)
        bass_label_layout.addStretch()
        bass_layout.addLayout(bass_label_layout)

        bass_control_layout = QHBoxLayout()
        self.bass_minus_btn = QPushButton("-")
        self.bass_minus_btn.setFixedWidth(32)
        self.bass_minus_btn.clicked.connect(
            lambda: self.adjust_slider(self.bass_slider, -1, self.on_bass_changed))
        self.bass_slider = QSlider(Qt.Orientation.Horizontal)
        self.bass_slider.setMinimum(-10)
        self.bass_slider.setMaximum(10)
        self.bass_slider.setValue(0)
        self.bass_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.bass_slider.setTickInterval(1)
        self.bass_slider.sliderMoved.connect(self.on_bass_changed)
        self.bass_plus_btn = QPushButton("+")
        self.bass_plus_btn.setFixedWidth(32)
        self.bass_plus_btn.clicked.connect(
            lambda: self.adjust_slider(self.bass_slider, 1, self.on_bass_changed))
        bass_control_layout.addWidget(self.bass_minus_btn)
        bass_control_layout.addWidget(self.bass_slider)
        bass_control_layout.addWidget(self.bass_plus_btn)
        bass_layout.addLayout(bass_control_layout)
        self.bass_group.setLayout(bass_layout)
        layout.addWidget(self.bass_group)

    def _init_treble_section(self, layout: QVBoxLayout):
        self.treble_group = QGroupBox(tr('treble_group'))
        treble_layout = QVBoxLayout()
        treble_label_layout = QHBoxLayout()
        self._treble_level_label = QLabel(tr('treble_level'))
        treble_label_layout.addWidget(self._treble_level_label)
        self.treble_value_label = QLabel("0")
        self.treble_value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.treble_value_label.setStyleSheet("color: #764ba2;")
        treble_label_layout.addWidget(self.treble_value_label)
        treble_label_layout.addStretch()
        treble_layout.addLayout(treble_label_layout)

        treble_control_layout = QHBoxLayout()
        self.treble_minus_btn = QPushButton("-")
        self.treble_minus_btn.setFixedWidth(32)
        self.treble_minus_btn.clicked.connect(
            lambda: self.adjust_slider(self.treble_slider, -1, self.on_treble_changed))
        self.treble_slider = QSlider(Qt.Orientation.Horizontal)
        self.treble_slider.setMinimum(-10)
        self.treble_slider.setMaximum(10)
        self.treble_slider.setValue(0)
        self.treble_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.treble_slider.setTickInterval(1)
        self.treble_slider.sliderMoved.connect(self.on_treble_changed)
        self.treble_plus_btn = QPushButton("+")
        self.treble_plus_btn.setFixedWidth(32)
        self.treble_plus_btn.clicked.connect(
            lambda: self.adjust_slider(self.treble_slider, 1, self.on_treble_changed))
        treble_control_layout.addWidget(self.treble_minus_btn)
        treble_control_layout.addWidget(self.treble_slider)
        treble_control_layout.addWidget(self.treble_plus_btn)
        treble_layout.addLayout(treble_control_layout)
        self.treble_group.setLayout(treble_layout)
        layout.addWidget(self.treble_group)

    def _init_loudness_section(self, layout: QVBoxLayout):
        self.loudness_group = QGroupBox(tr('loudness_group'))
        loudness_layout = QHBoxLayout()
        self.loudness_checkbox = QCheckBox(tr('enable_loudness'))
        self.loudness_checkbox.toggled.connect(self.on_loudness_changed)
        loudness_layout.addWidget(self.loudness_checkbox)
        loudness_layout.addStretch()
        self.loudness_group.setLayout(loudness_layout)
        layout.addWidget(self.loudness_group)

    def _init_audio_options_section(self, layout: QVBoxLayout):
        self.audio_opts_group = QGroupBox(tr('audio_opts_group'))
        audio_opts_layout = QVBoxLayout()
        self.speech_enhancement_checkbox = QCheckBox(tr('speech_enhancement'))
        self.speech_enhancement_checkbox.toggled.connect(
            self.on_speech_enhancement_changed)
        self.night_mode_checkbox = QCheckBox(tr('night_sound'))
        self.night_mode_checkbox.toggled.connect(self.on_night_mode_changed)
        self.cross_fade_checkbox = QCheckBox(tr('cross_fade'))
        self.cross_fade_checkbox.toggled.connect(self.on_cross_fade_changed)
        audio_opts_layout.addWidget(self.speech_enhancement_checkbox)
        audio_opts_layout.addWidget(self.night_mode_checkbox)
        audio_opts_layout.addWidget(self.cross_fade_checkbox)
        self.audio_opts_group.setLayout(audio_opts_layout)
        layout.addWidget(self.audio_opts_group)

    def _init_volume_section(self, layout: QVBoxLayout):
        self.volume_group = QGroupBox(tr('volume_group'))
        volume_layout = QVBoxLayout()
        volume_label_layout = QHBoxLayout()
        self._volume_label = QLabel(tr('volume_label'))
        volume_label_layout.addWidget(self._volume_label)
        self.volume_value_label = QLabel("50")
        self.volume_value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.volume_value_label.setStyleSheet("color: #4CAF50;")
        volume_label_layout.addWidget(self.volume_value_label)
        volume_label_layout.addStretch()
        volume_layout.addLayout(volume_label_layout)

        volume_control_layout = QHBoxLayout()
        self.volume_minus_btn = QPushButton("-")
        self.volume_minus_btn.setFixedWidth(32)
        self.volume_minus_btn.clicked.connect(
            lambda: self.adjust_slider(self.volume_slider, -6, self.on_volume_changed))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.sliderMoved.connect(self.on_volume_changed)
        self.volume_plus_btn = QPushButton("+")
        self.volume_plus_btn.setFixedWidth(32)
        self.volume_plus_btn.clicked.connect(
            lambda: self.adjust_slider(self.volume_slider, 6, self.on_volume_changed))
        volume_control_layout.addWidget(self.volume_minus_btn)
        volume_control_layout.addWidget(self.volume_slider)
        volume_control_layout.addWidget(self.volume_plus_btn)
        volume_layout.addLayout(volume_control_layout)
        self.volume_group.setLayout(volume_layout)
        layout.addWidget(self.volume_group)

    def _init_presets_section(self, layout: QVBoxLayout):
        self._preset_group = QGroupBox(tr('presets_group'))
        preset_layout = QVBoxLayout()
        self.preset_list = QListWidget()
        self.preset_list.setMaximumHeight(160)
        self.update_preset_list()
        self.preset_list.itemClicked.connect(self.on_preset_selected)
        preset_layout.addWidget(self.preset_list)

        preset_button_layout = QHBoxLayout()
        self._new_preset_btn = QPushButton(tr('new_preset_btn'))
        self._new_preset_btn.clicked.connect(self.create_new_preset)
        self._edit_preset_btn = QPushButton(tr('edit_preset_btn'))
        self._edit_preset_btn.clicked.connect(self.edit_preset)
        self._delete_preset_btn = QPushButton(tr('delete_preset_btn'))
        self._delete_preset_btn.clicked.connect(self.delete_preset)
        preset_button_layout.addWidget(self._new_preset_btn)
        preset_button_layout.addWidget(self._edit_preset_btn)
        preset_button_layout.addWidget(self._delete_preset_btn)
        preset_layout.addLayout(preset_button_layout)
        self._preset_group.setLayout(preset_layout)
        layout.addWidget(self._preset_group)

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr('status_ready'))
        self._quit_btn = QPushButton(tr('quit_btn'))
        self._quit_btn.setFixedHeight(20)
        self._quit_btn.setStyleSheet(
            "QPushButton { color: #f44336; border: none; padding: 0 6px; }")
        self._quit_btn.clicked.connect(self.quit_app)
        self.status_bar.addPermanentWidget(self._quit_btn)

    def open_settings_dialog(self):
        SettingsDialog(self).exec()

    def load_device_cache(self) -> bool:
        """キャッシュからデバイスリストを復元。成功したらTrueを返す
        Restore device list from cache. Returns True on success."""
        import json
        if not os.path.exists(DEVICE_CACHE_PATH):
            return False
        try:
            with open(DEVICE_CACHE_PATH, 'r', encoding='utf-8') as f:
                device_info = json.load(f)
            if not device_info:
                return False
            self.device_combo.clear()
            for dev in device_info:
                self.device_combo.addItem(
                    f"{dev['name']} ({dev['ip']})", dev['ip'])
            self.status_bar.showMessage(
                tr('status_loaded_devices', n=len(device_info)))
            self.on_device_selected()
            return True
        except Exception:
            # 壊れたキャッシュは削除して次回スキャン時に再作成 / Delete corrupted cache; it will be recreated on the next scan
            try:
                os.remove(DEVICE_CACHE_PATH)
            except OSError:
                pass
            return False

    def save_device_cache(self, device_info: list):
        """デバイスリストをキャッシュに保存 / Save device list to cache"""
        import json
        import tempfile
        tmp = DEVICE_CACHE_PATH + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(device_info, f)
            os.replace(tmp, DEVICE_CACHE_PATH)
        except Exception:
            pass

    def discover_devices(self):
        """デバイスを検出"""
        reply = QMessageBox.question(
            self,
            tr('scan_confirm_title'),
            tr('scan_confirm_msg'),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return

        self.scan_button.setText(tr('scan_btn_scanning'))
        self.scan_button.setEnabled(False)
        self.device_combo.clear()
        self.device_combo.addItem(tr('discovering'))

        def get_arp_ips() -> list:
            """arp -a からアクティブなIPアドレス一覧を取得 / Get active IP addresses from arp -a"""
            import subprocess
            import re
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True, text=True
            )
            ips = re.findall(r'\((\d+\.\d+\.\d+\.\d+)\)', result.stdout)
            # ブロードキャスト・マルチキャストを除外 / Exclude broadcast and multicast addresses
            return [ip for ip in ips if not ip.startswith(('224.', '239.', '255.'))]

        def run_discover():
            try:
                found = discover()
                devices = list(found) if found is not None else []

                # マルチキャストで見つからない場合はarpで取得したIPのみスキャン
                # Fall back to scanning ARP-discovered IPs when multicast yields nothing
                if not devices:
                    arp_ips = get_arp_ips()
                    n = len(arp_ips)
                    self._discover_status.emit(
                        tr('status_multicast_fail', n=n))
                    for i, ip in enumerate(arp_ips, 1):
                        self._discover_status.emit(
                            tr('status_scanning_ip', ip=ip, i=i, n=n))
                        try:
                            d = SoCo(ip)
                            _ = d.player_name
                            devices.append(d)
                        except Exception:
                            pass

                device_info = []
                for device in devices:
                    try:
                        device_info.append({
                            'name': device.player_name,
                            'ip': device.ip_address
                        })
                    except Exception:
                        device_info.append({
                            'name': device.ip_address,
                            'ip': device.ip_address
                        })

                if device_info:
                    self.save_device_cache(device_info)

                self._discover_done.emit(device_info)
            except Exception as e:
                self._discover_error.emit(f"Error: {e}")

        thread = threading.Thread(target=run_discover, daemon=True)
        thread.start()

    def _on_discover_status(self, msg: str):
        """スキャン進捗 — GUIスレッドで実行される / Scan progress — runs on the GUI thread"""
        self.status_bar.showMessage(msg)

    def _on_discover_done(self, device_info: list):
        """スキャン完了 — GUIスレッドで実行される / Scan complete — runs on the GUI thread"""
        self.device_combo.clear()
        if device_info:
            for dev in device_info:
                self.device_combo.addItem(
                    f"{dev['name']} ({dev['ip']})", dev['ip'])
            self.status_bar.showMessage(
                tr('status_found_devices', n=len(device_info)))
            self.on_device_selected()
        else:
            self.device_combo.addItem(tr('no_devices_combo'))
            self.status_bar.showMessage(tr('status_no_sonos'))
        self.scan_button.setText(tr('scan_btn'))
        self.scan_button.setEnabled(True)

    def _on_discover_error(self, msg: str):
        """スキャンエラー — GUIスレッドで実行される / Scan error — runs on the GUI thread"""
        self.device_combo.clear()
        self.device_combo.addItem(tr('discovery_error_combo'))
        self.status_bar.showMessage(msg)
        self.scan_button.setText(tr('scan_btn'))
        self.scan_button.setEnabled(True)

    def on_device_selected(self):
        """デバイスが選択された / Called when a device is selected from the combo box"""
        if self.device_combo.count() == 0:
            return

        ip_address = self.device_combo.currentData()
        if not ip_address:
            return

        try:
            self.controller = SonosEQController(ip_address)
            self.status_bar.showMessage(
                tr('status_connected', name=self.controller.device.player_name))
            self.refresh_eq_settings()
            self._refresh_track_info()
        except Exception as e:
            self.status_bar.showMessage(f"Error: {e}")

    def adjust_slider(self, slider: QSlider, delta: int, handler):
        """スライダーを1ステップ増減して即座に反映 / Nudge slider by delta and apply immediately"""
        new_value = max(slider.minimum(), min(
            slider.maximum(), slider.value() + delta))
        slider.setValue(new_value)
        handler(new_value)

    def check_feature_availability(self):
        """各機能の利用可否をチェックしてUIを有効/無効化する
        Check which EQ features the device supports and enable/disable UI accordingly."""
        if self.controller is None:
            return
        device = self.controller.device

        def check():
            def try_get(fn):
                try:
                    fn()
                    return True
                except Exception:
                    return False

            results = {
                'bass':               try_get(lambda: device.bass),
                'treble':             try_get(lambda: device.treble),
                'loudness':           try_get(lambda: device.loudness),
                'speech_enhancement': try_get(lambda: device.speech_enhance_enabled),
                'night_mode':         try_get(lambda: device.night_mode),
                'volume':             try_get(lambda: device.volume),
            }

            # GUIスレッドへ反映 / Apply results on the GUI thread
            def apply():
                self.bass_group.setEnabled(results['bass'])
                self.treble_group.setEnabled(results['treble'])
                self.loudness_group.setEnabled(results['loudness'])
                self.speech_enhancement_checkbox.setEnabled(
                    results['speech_enhancement'])
                self.night_mode_checkbox.setEnabled(results['night_mode'])
                self.volume_group.setEnabled(results['volume'])
                unavailable = [k for k, v in results.items() if not v]
                if unavailable:
                    self.status_bar.showMessage(
                        tr('status_unavailable', features=', '.join(unavailable)))
                else:
                    self.status_bar.showMessage(tr('status_all_available'))

            QTimer.singleShot(0, apply)

        threading.Thread(target=check, daemon=True).start()

    def _apply_setting_async(self, setter, status_msg: str,
                             value_label=None, display_value: str = ''):
        """設定変更を非同期スレッドで実行する共通ヘルパー。
        setter(controller) を呼び出し、完了後に update_in_progress を解除する。
        Common helper to apply a setting change on a background thread.
        Calls setter(controller) and clears update_in_progress when done."""
        if value_label is not None:
            value_label.setText(display_value)
        if self.controller is None or self.update_in_progress:
            return
        self.update_in_progress = True
        self.status_bar.showMessage(status_msg)
        controller = self.controller

        def run():
            try:
                setter(controller)
            except Exception as e:
                self.status_bar.showMessage(f"Error: {e}")

        threading.Thread(target=run, daemon=True).start()
        QTimer.singleShot(500, lambda: setattr(
            self, 'update_in_progress', False))

    def on_speech_enhancement_changed(self, checked):
        self._apply_setting_async(
            lambda c: c.set_speech_enhancement(checked),
            tr('status_setting_speech', state=tr(
                'state_on' if checked else 'state_off')),
        )

    def on_night_mode_changed(self, checked):
        self._apply_setting_async(
            lambda c: c.set_night_mode(checked),
            tr('status_setting_night', state=tr(
                'state_on' if checked else 'state_off')),
        )

    def on_volume_changed(self, value):
        self._volume_hud.show_volume(value)
        self._apply_setting_async(
            lambda c: c.set_volume(value),
            tr('status_setting_volume', value=value),
            self.volume_value_label, str(value),
        )

    def on_bass_changed(self, value):
        self._apply_setting_async(
            lambda c: c.set_bass(value),
            tr('status_setting_bass', value=value),
            self.bass_value_label, str(value),
        )

    def on_treble_changed(self, value):
        self._apply_setting_async(
            lambda c: c.set_treble(value),
            tr('status_setting_treble', value=value),
            self.treble_value_label, str(value),
        )

    def on_loudness_changed(self, checked):
        self._apply_setting_async(
            lambda c: c.set_loudness(checked),
            tr('status_setting_loudness', state=tr(
                'state_on' if checked else 'state_off')),
        )

    def refresh_eq_settings(self):
        if self.controller is None:
            return
        self.status_bar.showMessage(tr('status_updating_eq'))
        controller = self.controller

        def fetch():
            try:
                settings = controller.get_all_eq_settings()
                self._settings_ready.emit(settings)
            except Exception as e:
                self._settings_ready.emit({'_error': str(e)})

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_settings(self, settings: dict):
        """メインスレッドでUIに設定値を反映する（シグナル経由で呼ばれる）
        Apply fetched EQ settings to the UI on the main thread (called via signal)."""
        if '_error' in settings:
            self.status_bar.showMessage(f"Error: {settings['_error']}")
            return

        widgets = [
            self.bass_slider, self.treble_slider,
            self.loudness_checkbox, self.speech_enhancement_checkbox,
            self.night_mode_checkbox, self.volume_slider,
            self.cross_fade_checkbox, self.shuffle_button,
        ]
        for w in widgets:
            w.blockSignals(True)

        if settings['bass'] is not None:
            self.bass_slider.setValue(settings['bass'])
            self.bass_value_label.setText(str(settings['bass']))
        self.bass_group.setEnabled(settings['bass'] is not None)

        if settings['treble'] is not None:
            self.treble_slider.setValue(settings['treble'])
            self.treble_value_label.setText(str(settings['treble']))
        self.treble_group.setEnabled(settings['treble'] is not None)

        if settings['loudness'] is not None:
            self.loudness_checkbox.setChecked(settings['loudness'])
        self.loudness_group.setEnabled(settings['loudness'] is not None)

        if settings['speech_enhancement'] is not None:
            self.speech_enhancement_checkbox.setChecked(
                settings['speech_enhancement'])
        self.speech_enhancement_checkbox.setEnabled(
            settings['speech_enhancement'] is not None)

        if settings['night_mode'] is not None:
            self.night_mode_checkbox.setChecked(settings['night_mode'])
        self.night_mode_checkbox.setEnabled(settings['night_mode'] is not None)

        if settings['volume'] is not None:
            self.volume_slider.setValue(settings['volume'])
            self.volume_value_label.setText(str(settings['volume']))
        self.volume_group.setEnabled(settings['volume'] is not None)

        if settings.get('cross_fade') is not None:
            self.cross_fade_checkbox.setChecked(settings['cross_fade'])
        self.cross_fade_checkbox.setEnabled(
            settings.get('cross_fade') is not None)

        if settings.get('shuffle') is not None:
            self.shuffle_button.setChecked(settings['shuffle'])
        self.shuffle_button.setEnabled(settings.get('shuffle') is not None)

        if settings.get('repeat') is not None:
            self._repeat_mode = settings['repeat']
            _repeat_labels = {
                'off': tr('repeat_off'),
                'all': tr('repeat_all'),
                'one': tr('repeat_one'),
            }
            self.repeat_button.setText(
                _repeat_labels.get(self._repeat_mode, tr('repeat_off')))
        self.repeat_button.setEnabled(settings.get('repeat') is not None)

        for w in widgets:
            w.blockSignals(False)

        self.status_bar.showMessage(tr('status_eq_updated'))

    def reset_eq_settings(self):
        if self.controller is None:
            return

        reply = QMessageBox.question(
            self,
            tr('reset_eq_title'),
            tr('reset_eq_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage(tr('status_resetting_eq'))

            def reset():
                try:
                    self.controller.set_bass(0)
                    self.controller.set_treble(0)
                    self.controller.set_loudness(False)
                    self.refresh_eq_settings()
                except Exception as e:
                    self.status_bar.showMessage(f"Error: {e}")

            thread = threading.Thread(target=reset, daemon=True)
            thread.start()

    def update_preset_list(self):
        """プリセットリストを更新 / Refresh the preset list widget"""
        self.preset_list.clear()
        for preset in self.presets:
            item = QListWidgetItem(f"🎚️  {preset.name}")
            self.preset_list.addItem(item)

    def on_preset_selected(self, item):
        """プリセットが選択されたら即座に適用 / Apply the selected preset immediately"""
        index = self.preset_list.row(item)
        if 0 <= index < len(self.presets):
            self.selected_preset_index = index
            self.apply_preset(index)

    def apply_preset(self, index: int):
        """プリセットを適用 / Apply the preset at the given index"""
        if self.controller is None:
            QMessageBox.warning(self, tr('warn_title'), tr('warn_no_device'))
            return

        preset = self.presets[index]
        self.status_bar.showMessage(
            tr('status_applying_preset', name=preset.name))
        controller = self.controller

        def apply():
            try:
                controller.set_bass(preset.bass)
                controller.set_treble(preset.treble)
                controller.set_loudness(preset.loudness)
                controller.set_speech_enhancement(preset.speech_enhancement)
                controller.set_night_mode(preset.night_mode)
                self.refresh_eq_settings()
                self.status_bar.showMessage(
                    tr('status_preset_applied', name=preset.name))
            except Exception as e:
                self.status_bar.showMessage(f"Error: {e}")

        threading.Thread(target=apply, daemon=True).start()

    def create_new_preset(self):
        """新しいプリセットを作成 / Open dialog to create a new preset"""
        dialog = PresetDialog(self)
        if dialog.exec():
            preset = dialog.get_preset()
            self.presets.append(preset)
            save_presets(self.presets)
            self.update_preset_list()
            self.status_bar.showMessage(
                tr('status_preset_created', name=preset.name))

    def edit_preset(self):
        """選択中のプリセットを編集 / Open dialog to edit the selected preset"""
        if self.selected_preset_index is None:
            QMessageBox.warning(
                self, tr('warn_title'), tr('warn_select_preset'))
            return

        index = self.selected_preset_index
        dialog = PresetDialog(self, preset=self.presets[index])
        if dialog.exec():
            self.presets[index] = dialog.get_preset()
            save_presets(self.presets)
            self.update_preset_list()
            self.preset_list.setCurrentRow(index)
            self.status_bar.showMessage(
                tr('status_preset_updated', name=self.presets[index].name))

    def delete_preset(self):
        """プリセットを削除 / Delete the selected preset after confirmation"""
        if self.selected_preset_index is None:
            QMessageBox.warning(
                self, tr('warn_title'), tr('warn_select_preset'))
            return

        index = self.selected_preset_index
        preset_name = self.presets[index].name
        reply = QMessageBox.question(
            self, tr('delete_preset_title'), tr(
                'delete_preset_msg', name=preset_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.presets.pop(index)
            save_presets(self.presets)
            self.update_preset_list()
            self.status_bar.showMessage(
                tr('status_preset_deleted', name=preset_name))

    # ── キーボード制御 / Keyboard & media key control ──────────────────────────────────────────

    def _start_keyboard_listener(self):
        if not PYNPUT_AVAILABLE:
            self.status_bar.showMessage(tr('status_pynput_disabled'))
            return

        def on_press(key):
            if key == pynput_keyboard.Key.media_volume_up:
                self._media_key_pressed.emit("volume_up")
            elif key == pynput_keyboard.Key.media_volume_down:
                self._media_key_pressed.emit("volume_down")
            elif key == pynput_keyboard.Key.media_play_pause:
                self._media_key_pressed.emit("play_pause")
            elif key == pynput_keyboard.Key.media_next:
                self._media_key_pressed.emit("next_track")
            elif key == pynput_keyboard.Key.media_previous:
                self._media_key_pressed.emit("previous_track")

        self._keyboard_listener = pynput_keyboard.Listener(
            on_press=on_press, suppress=False
        )
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

    def _handle_media_key(self, key_name: str):
        if self.controller is None:
            return

        uri = self._current_uri
        # AirPlay / 光デジタル / ライン入力など、Sonos経由でトラック操作できないソース。
        # Apple MusicやSpotify等の外部アプリへの制御は行わない（設計方針）。
        # Sources where track control via Sonos is not available (AirPlay, optical, line-in).
        # External apps such as Apple Music or Spotify are never controlled (by design).
        is_uncontrollable = (
            uri.startswith(self.controller._UNCONTROLLABLE_PREFIXES)
            or self._is_airplay_stream()
        )

        if key_name == "volume_up":
            self.adjust_slider(self.volume_slider, 6, self.on_volume_changed)
            self.status_bar.showMessage(
                tr('status_volume', value=self.volume_slider.value()))

        elif key_name == "volume_down":
            self.adjust_slider(self.volume_slider, -6, self.on_volume_changed)
            self.status_bar.showMessage(
                tr('status_volume', value=self.volume_slider.value()))

        elif key_name == "play_pause":
            if is_uncontrollable:
                self.status_bar.showMessage(tr('key_play_pause_blocked'))
                return
            self._toggle_playback()

        elif key_name == "next_track":
            if is_uncontrollable:
                self.status_bar.showMessage(tr('key_next_blocked'))
                return
            controller = self.controller

            def skip():
                try:
                    controller.next_track()
                    QTimer.singleShot(
                        0, lambda: self.status_bar.showMessage(tr('status_next_track')))
                except Exception as e:
                    msg = f"Error: {e}"
                    QTimer.singleShot(
                        0, lambda m=msg: self.status_bar.showMessage(m))

            threading.Thread(target=skip, daemon=True).start()

        elif key_name == "previous_track":
            if is_uncontrollable:
                self.status_bar.showMessage(tr('key_prev_blocked'))
                return
            controller = self.controller

            def rewind():
                try:
                    controller.previous_track()
                    QTimer.singleShot(
                        0, lambda: self.status_bar.showMessage(tr('status_prev_track')))
                except Exception as e:
                    msg = f"Error: {e}"
                    QTimer.singleShot(
                        0, lambda m=msg: self.status_bar.showMessage(m))

            threading.Thread(target=rewind, daemon=True).start()

    def retranslate_ui(self):
        """言語切替後に全UI文字列を更新する / Retranslate all UI strings after a language change"""
        self.setWindowTitle(tr('window_title'))
        self._device_label.setText(tr('device_label'))
        if self.scan_button.isEnabled():
            self.scan_button.setText(tr('scan_btn'))
        self.connect_button.setText(tr('connect_btn'))
        self._now_playing_group.setTitle(tr('now_playing_group'))
        self._playback_group.setTitle(tr('playback_group'))
        self.bass_group.setTitle(tr('bass_group'))
        self._bass_level_label.setText(tr('bass_level'))
        self.treble_group.setTitle(tr('treble_group'))
        self._treble_level_label.setText(tr('treble_level'))
        self.loudness_group.setTitle(tr('loudness_group'))
        self.loudness_checkbox.setText(tr('enable_loudness'))
        self.audio_opts_group.setTitle(tr('audio_opts_group'))
        self.speech_enhancement_checkbox.setText(tr('speech_enhancement'))
        self.night_mode_checkbox.setText(tr('night_sound'))
        self.cross_fade_checkbox.setText(tr('cross_fade'))
        _repeat_labels = {
            'off': tr('repeat_off'),
            'all': tr('repeat_all'),
            'one': tr('repeat_one'),
        }
        self.repeat_button.setText(
            _repeat_labels.get(self._repeat_mode, tr('repeat_off')))
        self.volume_group.setTitle(tr('volume_group'))
        self._volume_label.setText(tr('volume_label'))
        self._preset_group.setTitle(tr('presets_group'))
        self._new_preset_btn.setText(tr('new_preset_btn'))
        self._edit_preset_btn.setText(tr('edit_preset_btn'))
        self._delete_preset_btn.setText(tr('delete_preset_btn'))
        self._settings_button.setText(tr('settings_btn'))
        self._quit_btn.setText(tr('quit_btn'))

    def closeEvent(self, event):
        # ウィンドウを閉じてもアプリは終了しない（メニューバーアプリ）
        # Hide instead of quit — the app lives as a menu bar item
        event.ignore()
        self.hide()

    def quit_app(self):
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        QApplication.quit()

    # ── Now Playing / 再生情報 ────────────────────────────────────────────

    def _refresh_track_info(self):
        if self.controller is None:
            return
        controller = self.controller

        def fetch():
            try:
                info = controller.get_current_track_info()
                self._track_info_ready.emit(info)
            except Exception:
                pass

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_track_info(self, info: dict):
        controllable = info.get('_controllable', True)
        uri = info.get('uri', '')
        self._current_uri = uri

        # ソース名を判定してタイトルエリアに表示 / Determine source name and show it in the title area
        if not controllable:
            if uri.startswith('x-sonos-htastream:'):
                source = tr('source_tv')
            elif uri.startswith('x-rincon-stream:'):
                source = tr('source_line_in')
            else:
                source = tr('source_external')
            self.track_title_label.setText(source)
            self.track_artist_album_label.setText(tr('source_no_playback'))
        else:
            self.track_title_label.setText(info.get('title', '--') or '--')
            artist = info.get('artist', '') or ''
            album = info.get('album', '') or ''
            if artist and album:
                self.track_artist_album_label.setText(f"{artist}  -  {album}")
            elif artist:
                self.track_artist_album_label.setText(artist)
            elif album:
                self.track_artist_album_label.setText(album)
            else:
                self.track_artist_album_label.setText('--')

        for btn in (self.prev_button, self.play_pause_button, self.next_button):
            btn.setEnabled(controllable)

        state = info.get('_transport_state', '')
        if self._is_airplay_stream():
            # AirPlay中はミュート状態でボタン表示を決定（pause/playは使わない）
            # During AirPlay, derive button label from mute state instead of play/pause
            muted = info.get('_muted', False)
            self.play_pause_button.setText("▶" if muted else "⏸")
        else:
            self.play_pause_button.setText("⏸" if state == 'PLAYING' else "▶")

        album_art_uri = info.get('album_art', '')
        if album_art_uri:
            def load_art(uri=album_art_uri):
                try:
                    import urllib.request
                    with urllib.request.urlopen(uri, timeout=5) as resp:
                        data = resp.read()
                    image = QImage()
                    image.loadFromData(data)
                    self._album_art_ready.emit(image)
                except Exception as e:
                    msg = f"Art error: {e}"
                    QTimer.singleShot(
                        0, lambda m=msg: self.status_bar.showMessage(m))
            threading.Thread(target=load_art, daemon=True).start()
        else:
            self.album_art_label.clear()
            self.album_art_label.setText(tr('no_image'))

    def _apply_album_art(self, image: QImage):
        self._album_art_pixmap = QPixmap.fromImage(image)
        self._rescale_album_art()

    def _rescale_album_art(self, available_width: int = 0):
        if not self._album_art_pixmap:
            return
        if available_width <= 0:
            available_width = self.album_art_label.width()
        w = max(50, available_width)
        scaled = self._album_art_pixmap.scaled(
            w, w,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.album_art_label.setFixedHeight(scaled.height())
        self.album_art_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # content margins(12*2) + groupbox margins(8*2) + groupbox border(~4) = ~44px
        # コンテンツマージン合計を差し引いてアルバムアートの利用幅を算出
        w = max(50, event.size().width() - 44)
        self._rescale_album_art(w)
        QTimer.singleShot(0, self._clamp_scroll_content_width)

    def _clamp_scroll_content_width(self):
        """コンテンツ幅をビューポート幅に合わせ、横スクロールを防ぐ
        Clamp content width to the viewport to prevent horizontal scrolling."""
        vp = self._scroll_area.viewport()
        widget = self._scroll_area.widget()
        if vp is None or widget is None:
            return
        widget.setMaximumWidth(vp.width())

    # ── 再生コントロール ボタン / Playback control buttons ──────────────────────────────────

    def _is_airplay_stream(self) -> bool:
        return 'airplay:' in self._current_uri

    def _do_mute_toggle(self, controller, on_muted, on_unmuted):
        """ミュート切替の共通ロジック（バックグラウンドスレッドから呼ぶ）。
        音量退避・復元を行い、完了後に on_muted / on_unmuted をGUIスレッドで実行する。
        Shared mute-toggle logic (call from a background thread).
        Saves/restores volume and fires on_muted / on_unmuted on the GUI thread."""
        muted = controller.get_mute()
        if not muted:
            self._pre_mute_volume = controller.get_volume()
            controller.set_mute(True)
            QTimer.singleShot(0, on_muted)
        else:
            controller.set_mute(False)
            if controller.get_volume() == 0 and self._pre_mute_volume:
                controller.set_volume(self._pre_mute_volume)
                vol = self._pre_mute_volume
                QTimer.singleShot(
                    0, lambda v=vol: self.volume_slider.setValue(v))
                QTimer.singleShot(
                    0, lambda v=vol: self.volume_value_label.setText(str(v)))
            self._pre_mute_volume = None
            QTimer.singleShot(0, on_unmuted)

    def _toggle_playback(self):
        """AirPlayストリーム中はミュートで代替し、pause()によるセッション切断を防ぐ
        Use mute instead of pause during AirPlay to avoid disconnecting the AirPlay session."""
        if self.controller is None:
            return
        controller = self.controller
        is_airplay = self._is_airplay_stream()

        def toggle():
            try:
                if is_airplay:
                    def _on_muted():
                        self.play_pause_button.setText("▶")
                        self.status_bar.showMessage(tr('status_muted_airplay'))

                    def _on_unmuted():
                        self.play_pause_button.setText("⏸")
                        self.status_bar.showMessage(
                            tr('status_unmuted_airplay'))

                    self._do_mute_toggle(controller, _on_muted, _on_unmuted)
                else:
                    if controller.is_playing():
                        controller.pause()
                        QTimer.singleShot(
                            0, lambda: self.play_pause_button.setText("▶"))
                        QTimer.singleShot(
                            0, lambda: self.status_bar.showMessage(tr('status_paused')))
                    else:
                        controller.play()
                        QTimer.singleShot(
                            0, lambda: self.play_pause_button.setText("⏸"))
                        QTimer.singleShot(
                            0, lambda: self.status_bar.showMessage(tr('status_playing')))
            except Exception as e:
                msg = f"Error: {e}"
                QTimer.singleShot(
                    0, lambda m=msg: self.status_bar.showMessage(m))

        threading.Thread(target=toggle, daemon=True).start()

    def _on_prev_clicked(self):
        if self.controller is None:
            return
        controller = self.controller

        def go():
            try:
                controller.previous_track()
                QTimer.singleShot(1000, self._refresh_track_info)
            except Exception as e:
                msg = f"Error: {e}"
                QTimer.singleShot(
                    0, lambda m=msg: self.status_bar.showMessage(m))

        threading.Thread(target=go, daemon=True).start()

    def _on_play_pause_clicked(self):
        self._toggle_playback()

    def _on_next_clicked(self):
        if self.controller is None:
            return
        controller = self.controller

        def go():
            try:
                controller.next_track()
                QTimer.singleShot(1000, self._refresh_track_info)
            except Exception as e:
                msg = f"Error: {e}"
                QTimer.singleShot(
                    0, lambda m=msg: self.status_bar.showMessage(m))

        threading.Thread(target=go, daemon=True).start()

    def _on_mute_clicked(self):
        if self.controller is None:
            return
        controller = self.controller

        def _on_muted():
            self.mute_button.setStyleSheet("color: #f44336;")
            self.status_bar.showMessage(tr('status_muted'))

        def _on_unmuted():
            self.mute_button.setStyleSheet("")
            self.status_bar.showMessage(tr('status_unmuted'))

        def toggle():
            try:
                self._do_mute_toggle(controller, _on_muted, _on_unmuted)
            except Exception as e:
                msg = f"Error: {e}"
                QTimer.singleShot(
                    0, lambda m=msg: self.status_bar.showMessage(m))

        threading.Thread(target=toggle, daemon=True).start()

    def on_cross_fade_changed(self, checked: bool):
        self._apply_setting_async(
            lambda c: c.set_cross_fade(checked),
            tr('status_setting_crossfade',
               state=tr('state_on' if checked else 'state_off')),
        )

    def _on_shuffle_clicked(self):
        if self.controller is None:
            return
        checked = self.shuffle_button.isChecked()
        self._apply_setting_async(
            lambda c: c.set_shuffle(checked),
            tr('status_setting_shuffle',
               state=tr('state_on' if checked else 'state_off')),
        )

    def _on_repeat_clicked(self):
        if self.controller is None:
            return
        _cycle = {'off': 'all', 'all': 'one', 'one': 'off'}
        _labels = {
            'off': tr('repeat_off'),
            'all': tr('repeat_all'),
            'one': tr('repeat_one'),
        }
        next_mode = _cycle.get(self._repeat_mode, 'all')
        self._repeat_mode = next_mode
        self.repeat_button.setText(_labels[next_mode])
        self._apply_setting_async(
            lambda c, m=next_mode: c.set_repeat(m),
            tr('status_setting_repeat', state=_labels[next_mode]),
        )


def _make_tray_icon() -> QIcon:
    """メニューバー用アイコンを単色（モノクロ）で生成する
    Generate a monochrome menu bar icon programmatically."""
    # 1. キャンバスの作成 (30x30) / Create a 30x30 canvas
    pix = QPixmap(30, 30)
    pix.fill(Qt.GlobalColor.transparent)  # 背景を透明に / Fill with transparent background

    # 2. 筆(QPainter)の準備 / Set up QPainter
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 3. ペン（色）を設定 / Set pen color (white for dark menu bar)
    p.setPen(Qt.GlobalColor.white)

    # 4. フォントを設定 — 標準フォントで▶などの記号を単色描画できる
    # Use a standard font (Arial) to render symbols like ▶ in a single color
    p.setFont(QFont("Arial", 26))

    # 5. 描画 — U+25B6 再生記号 / Draw U+25B6 PLAY symbol
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "\u25B6")

    p.end()
    icon = QIcon(pix)
    icon.setIsMask(True)  # アイコン全体をマスクとして扱う / Treat as template image (macOS dark/light mode aware)
    return QIcon(pix)


def _check_accessibility_permission() -> bool:
    """アクセシビリティ権限を確認し、未許可なら許可ダイアログを表示する。
    戻り値: True=権限あり / False=権限なし（ユーザーに再起動を促した）
    Check Accessibility permission and prompt if not yet granted.
    Returns True if trusted, False if the user still needs to grant access."""
    try:
        # type: ignore[attr-defined]
        from ApplicationServices import AXIsProcessTrustedWithOptions
    except ImportError:
        return True  # ApplicationServices が使えない環境ではスキップ

    trusted = AXIsProcessTrustedWithOptions(
        {"AXTrustedCheckOptionPrompt": True})
    return bool(trusted)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)

    # Accessory policy 切り替え前にアクセシビリティ権限を確認する。
    # Regular policy のうちに呼ばないと許可ダイアログが表示されない。
    # Must be called before switching to Accessory activation policy;
    # the permission prompt only appears while the app is in Regular policy.
    if not _check_accessibility_permission():
        QMessageBox.information(
            None,
            tr('accessibility_title'),
            tr('accessibility_msg'),
        )
        sys.exit(0)

    # メニューバーアプリ化: Dockに表示せず、フルスクリーンを中断しない
    # Switch to Accessory policy: hide from Dock and avoid interrupting full-screen apps
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory)
    except ImportError:
        pass

    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
    _INSTANCE_KEY = "TuneRay-SingleInstance"
    probe = QLocalSocket()
    probe.connectToServer(_INSTANCE_KEY)
    if probe.waitForConnected(300):
        QMessageBox.warning(None, "TuneRay", tr('already_running'))
        sys.exit(0)

    _server = QLocalServer()
    QLocalServer.removeServer(_INSTANCE_KEY)
    _server.listen(_INSTANCE_KEY)

    gui = SonosEQGUIAdvanced()

    # メニューバーアイコン / Menu bar tray icon
    tray = QSystemTrayIcon(_make_tray_icon(), app)
    tray.setToolTip("TuneRay")

    def _position_below_tray():
        """ウィンドウをトレイアイコンの直下に配置する
        Position the main window directly below the tray icon."""
        icon_geo = tray.geometry()
        if icon_geo.isEmpty():
            # macOS では geometry() が空になることがある → カーソル位置で代用
            # geometry() can return an empty rect on macOS — fall back to cursor position
            cursor = QCursor.pos()
            icon_geo = QRect(cursor.x() - 11, 0, 22, 22)

        screen = QApplication.screenAt(
            icon_geo.center()) or QApplication.primaryScreen()
        avail = screen.availableGeometry()

        win_w = gui.width()
        win_h = gui.height()
        x = icon_geo.center().x() - win_w // 2
        y = icon_geo.bottom() + 4

        # 画面内に収める / Clamp to screen bounds
        x = max(avail.left(), min(x, avail.right() - win_w))
        y = max(avail.top(), min(y, avail.bottom() - win_h))
        gui.move(x, y)

    def toggle_window():
        if gui.isVisible():
            gui.hide()
        else:
            _position_below_tray()
            gui.show()
            gui.raise_()
            gui.activateWindow()

    tray.activated.connect(
        lambda reason: toggle_window()
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray.show()

    ret = app.exec()
    _server.close()
    sys.exit(ret)


if __name__ == "__main__":
    main()
