"""
TuneRay — i18n / アプリ設定

フレームワーク非依存。Qt・Tk どちらからでも import 可能。
"""

import json
import os
from typing import Optional

# ── データディレクトリ ──────────────────────────────────────────────────────────

def _get_data_dir() -> str:
    import platform
    if platform.system() == 'Windows':
        base = os.path.dirname(os.path.abspath(__file__))
    else:
        base = os.path.expanduser('~/Library/Application Support/TuneRay')
    os.makedirs(base, exist_ok=True)
    return base


_DATA_DIR = _get_data_dir()
APP_SETTINGS_PATH = os.path.join(_DATA_DIR, 'settings.json')


def _load_app_settings() -> dict:
    try:
        if os.path.exists(APP_SETTINGS_PATH):
            with open(APP_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_app_settings(settings: dict):
    try:
        with open(APP_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _detect_system_lang() -> str:
    import locale
    lang = locale.getdefaultlocale()[0] or ''
    return 'ja' if lang.startswith('ja') else 'en'


_app_settings: dict = _load_app_settings()
_LANG: str = _app_settings.get('language', _detect_system_lang())

# ── 翻訳文字列 ─────────────────────────────────────────────────────────────────

_STRINGS: dict = {
    'en': {
        'device_label': '🔊 Device:',
        'scan_btn': '🔍 Scan',
        'connect_btn': '🔌 Connect',
        'discovering': 'Discovering devices...',
        'no_devices_combo': 'No devices found',
        'discovery_error_combo': 'Discovery Error',
        'now_playing_group': 'Now Playing',
        'no_image': 'No Image',
        'playback_group': 'Playback Controls',
        'bass_group': 'Bass Control',
        'bass_level': 'Bass Level:',
        'treble_group': 'Treble Control',
        'treble_level': 'Treble Level:',
        'loudness_group': 'Loudness Compensation',
        'enable_loudness': 'Enable Loudness',
        'audio_opts_group': 'Audio Options',
        'speech_enhancement': 'Speech Enhancement',
        'night_sound': 'Night Sound',
        'cross_fade': 'Crossfade',
        'shuffle': 'Shuffle',
        'repeat_off': '—',
        'repeat_all': '🔁',
        'repeat_one': '🔂',
        'status_light': 'Status Light',
        'volume_group': 'Volume Control',
        'volume_label': 'Volume:',
        'presets_group': 'Presets',
        'new_preset_btn': '➕ New',
        'edit_preset_btn': '✏️  Edit',
        'delete_preset_btn': '🗑️  Delete',
        'settings_btn': '⚙️  Settings',
        'quit_btn': '✕ Quit',
        'status_ready': 'Ready',
        'status_loaded_devices': 'Loaded {n} device(s) from cache',
        'status_found_devices': 'Found {n} device(s)',
        'status_connected': 'Connected to {name}',
        'status_multicast_fail': 'Multicast discovery failed. Scanning {n} ARP hosts...',
        'status_scanning_ip': 'Scanning {ip} ... ({i}/{n})',
        'status_updating_eq': 'Updating EQ settings...',
        'status_eq_updated': 'EQ settings updated',
        'status_resetting_eq': 'Resetting EQ settings...',
        'status_all_available': 'All features available',
        'status_unavailable': 'Unavailable: {features}',
        'status_setting_bass': 'Setting Bass to {value}...',
        'status_setting_treble': 'Setting Treble to {value}...',
        'status_setting_volume': 'Setting Volume to {value}...',
        'status_setting_loudness': 'Setting Loudness to {state}...',
        'status_setting_speech': 'Setting Speech Enhancement to {state}...',
        'status_setting_night': 'Setting Night Sound to {state}...',
        'status_volume': 'Volume: {value}',
        'status_next_track': 'Next track',
        'status_prev_track': 'Previous track',
        'status_setting_crossfade': 'Setting Crossfade to {state}...',
        'status_setting_shuffle': 'Setting Shuffle to {state}...',
        'status_setting_repeat': 'Setting Repeat to {state}...',
        'status_setting_status_light': 'Setting Status Light to {state}...',
        'status_paused': 'Paused',
        'status_playing': 'Playing',
        'status_muted': 'Muted',
        'status_unmuted': 'Unmuted',
        'status_muted_airplay': 'Muted (AirPlay)',
        'status_unmuted_airplay': 'Unmuted (AirPlay)',
        'status_applying_preset': 'Applying preset: {name}',
        'status_preset_applied': "Preset '{name}' applied",
        'status_preset_created': "Preset '{name}' created",
        'status_preset_updated': "Preset '{name}' updated",
        'status_preset_deleted': "Preset '{name}' deleted",
        'status_pynput_disabled': 'pynput not installed — keyboard control disabled',
        'status_no_sonos': 'No SONOS devices found',
        'source_tv': 'TV Audio (HDMI ARC / Optical)',
        'source_line_in': 'Line Input',
        'source_external': 'External Input',
        'source_no_playback': 'Playback control unavailable',
        'key_play_pause_blocked': 'Play/Pause: Cannot control this input source',
        'key_next_blocked': 'Next Track: Cannot control this input source',
        'key_prev_blocked': 'Previous Track: Cannot control this input source',
        'warn_title': 'Warning',
        'warn_no_device': 'No device connected',
        'warn_select_preset': 'Please select a preset first',
        'reset_eq_title': 'Reset EQ Settings',
        'reset_eq_msg': 'Reset all EQ settings to default (Bass: 0, Treble: 0, Loudness: OFF)?',
        'delete_preset_title': 'Delete Preset',
        'delete_preset_msg': "Delete '{name}'?",
        'preset_dialog_title': 'EQ Preset',
        'preset_name_label': 'Preset Name:',
        'preset_bass_label': 'Bass:',
        'preset_treble_label': 'Treble:',
        'preset_loudness_label': 'Loudness:',
        'preset_speech_label': 'Speech Enhancement:',
        'preset_night_label': 'Night Sound:',
        'enable_checkbox': 'Enable',
        'ok_btn': 'OK',
        'cancel_btn': 'Cancel',
        'settings_title': 'Settings',
        'settings_device_status_group': 'Device Status',
        'settings_device_name_default': 'Device Name: --',
        'settings_ip_default': 'IP Address: --',
        'settings_status_disconnected': 'Status: 🔴 Disconnected',
        'settings_status_connected': 'Status: 🟢 Connected',
        'settings_status_error': 'Status: 🔴 Error: {e}',
        'settings_device_name': 'Device Name: {name}',
        'settings_ip': 'IP Address: {ip}',
        'settings_eq_group': 'EQ Controls',
        'settings_refresh_btn': '🔄 Refresh',
        'settings_reset_btn': '↩️  Reset to Default',
        'settings_about_group': 'About',
        'settings_close_btn': 'Close',
        'settings_lang_group': 'Language',
        'accessibility_title': 'TuneRay — Accessibility Permission Required',
        'accessibility_msg': (
            'Media keys (volume, playback) require Accessibility permission.\n\n'
            'System Settings → Privacy & Security → Accessibility\n'
            'Allow TuneRay (or Python), then restart the app.'
        ),
        'scan_confirm_title': 'Device Scan',
        'scan_confirm_msg': (
            'Scanning for SONOS devices may take up to 1–2 minutes '
            '(multicast + ARP host scan).\n\nProceed?'
        ),
        'scan_btn_scanning': '⏳ Scanning...',
        'already_running': 'TuneRay is already running.',
        'window_title': 'SONOS RAY Equalizer Controller Pro',
        'about_text': (
            '<b>SONOS RAY Equalizer Controller</b><br/><br/>'
            'PyQt6-based equalizer controller for SONOS RAY speakers.<br/><br/>'
            '<b>Features:</b><ul>'
            '<li>Now Playing display (album art, title, artist)</li>'
            '<li>Playback controls (play/pause, skip, mute, volume)</li>'
            '<li>AirPlay stream support (mute as substitute)</li>'
            '<li>Bass / Treble / Volume control (macOS-compatible steps)</li>'
            '<li>Loudness / Speech Enhancement / Night Sound toggles</li>'
            '<li>EQ preset management (create, edit, delete)</li>'
            '<li>Multi-device management (auto-discover + IP cache)</li>'
            '<li>Global media key control</li>'
            '</ul><b>Requirements:</b><ul>'
            '<li>Python 3.8+</li><li>PyQt6 / SoCo / pynput</li>'
            '<li>SONOS device on the same network</li>'
            '</ul><b>License:</b> MIT'
        ),
        'state_on': 'ON',
        'state_off': 'OFF',
    },
    'ja': {
        'device_label': '🔊 デバイス:',
        'scan_btn': '🔍 スキャン',
        'connect_btn': '🔌 接続',
        'discovering': 'デバイスを検索中...',
        'no_devices_combo': 'デバイスが見つかりません',
        'discovery_error_combo': '検索エラー',
        'now_playing_group': '再生中',
        'no_image': '画像なし',
        'playback_group': '再生コントロール',
        'bass_group': '低音コントロール',
        'bass_level': '低音レベル:',
        'treble_group': '高音コントロール',
        'treble_level': '高音レベル:',
        'loudness_group': 'ラウドネス補正',
        'enable_loudness': 'ラウドネスを有効にする',
        'audio_opts_group': 'オーディオオプション',
        'speech_enhancement': 'スピーチ強調',
        'night_sound': 'ナイトサウンド',
        'cross_fade': 'クロスフェード',
        'shuffle': 'シャッフル',
        'repeat_off': '—',
        'repeat_all': '🔁',
        'repeat_one': '🔂',
        'status_light': 'ステータスライト',
        'volume_group': '音量コントロール',
        'volume_label': '音量:',
        'presets_group': 'プリセット',
        'new_preset_btn': '➕ 新規',
        'edit_preset_btn': '✏️  編集',
        'delete_preset_btn': '🗑️  削除',
        'settings_btn': '⚙️  設定',
        'quit_btn': '✕ 終了',
        'status_ready': '準備完了',
        'status_loaded_devices': 'キャッシュから {n} 台のデバイスを読み込みました',
        'status_found_devices': '{n} 台のデバイスが見つかりました',
        'status_connected': '{name} に接続しました',
        'status_multicast_fail': 'マルチキャスト検索に失敗。{n} 台のARPホストをスキャン中...',
        'status_scanning_ip': '{ip} をスキャン中... ({i}/{n})',
        'status_updating_eq': 'EQ設定を更新中...',
        'status_eq_updated': 'EQ設定を更新しました',
        'status_resetting_eq': 'EQ設定をリセット中...',
        'status_all_available': 'すべての機能が利用可能',
        'status_unavailable': '利用不可: {features}',
        'status_setting_bass': '低音を {value} に設定中...',
        'status_setting_treble': '高音を {value} に設定中...',
        'status_setting_volume': '音量を {value} に設定中...',
        'status_setting_loudness': 'ラウドネスを {state} に設定中...',
        'status_setting_speech': 'スピーチ強調を {state} に設定中...',
        'status_setting_night': 'ナイトサウンドを {state} に設定中...',
        'status_volume': '音量: {value}',
        'status_next_track': '次のトラック',
        'status_prev_track': '前のトラック',
        'status_setting_crossfade': 'クロスフェードを {state} に設定中...',
        'status_setting_shuffle': 'シャッフルを {state} に設定中...',
        'status_setting_repeat': 'リピートを {state} に設定中...',
        'status_setting_status_light': 'ステータスライトを {state} に設定中...',
        'status_paused': '一時停止',
        'status_playing': '再生中',
        'status_muted': 'ミュート',
        'status_unmuted': 'ミュート解除',
        'status_muted_airplay': 'ミュート (AirPlay)',
        'status_unmuted_airplay': 'ミュート解除 (AirPlay)',
        'status_applying_preset': 'プリセットを適用中: {name}',
        'status_preset_applied': "プリセット '{name}' を適用しました",
        'status_preset_created': "プリセット '{name}' を作成しました",
        'status_preset_updated': "プリセット '{name}' を更新しました",
        'status_preset_deleted': "プリセット '{name}' を削除しました",
        'status_pynput_disabled': 'pynput がインストールされていません — キーボード制御無効',
        'status_no_sonos': 'SONOSデバイスが見つかりません',
        'source_tv': 'TV音声 (HDMI ARC / 光デジタル)',
        'source_line_in': 'ライン入力',
        'source_external': '外部入力',
        'source_no_playback': '再生制御は使用できません',
        'key_play_pause_blocked': '再生/停止: この入力ソースでは操作できません',
        'key_next_blocked': '次トラック: この入力ソースでは操作できません',
        'key_prev_blocked': '前トラック: この入力ソースでは操作できません',
        'warn_title': '警告',
        'warn_no_device': 'デバイスに接続されていません',
        'warn_select_preset': '先にプリセットを選択してください',
        'reset_eq_title': 'EQ設定をリセット',
        'reset_eq_msg': 'すべてのEQ設定をデフォルトにリセットしますか？ (低音: 0, 高音: 0, ラウドネス: OFF)',
        'delete_preset_title': 'プリセットを削除',
        'delete_preset_msg': "'{name}' を削除しますか？",
        'preset_dialog_title': 'EQプリセット',
        'preset_name_label': 'プリセット名:',
        'preset_bass_label': '低音:',
        'preset_treble_label': '高音:',
        'preset_loudness_label': 'ラウドネス:',
        'preset_speech_label': 'スピーチ強調:',
        'preset_night_label': 'ナイトサウンド:',
        'enable_checkbox': '有効',
        'ok_btn': 'OK',
        'cancel_btn': 'キャンセル',
        'settings_title': '設定',
        'settings_device_status_group': 'デバイス状態',
        'settings_device_name_default': 'デバイス名: --',
        'settings_ip_default': 'IPアドレス: --',
        'settings_status_disconnected': '状態: 🔴 未接続',
        'settings_status_connected': '状態: 🟢 接続済み',
        'settings_status_error': '状態: 🔴 エラー: {e}',
        'settings_device_name': 'デバイス名: {name}',
        'settings_ip': 'IPアドレス: {ip}',
        'settings_eq_group': 'EQコントロール',
        'settings_refresh_btn': '🔄 更新',
        'settings_reset_btn': '↩️  デフォルトに戻す',
        'settings_about_group': 'このアプリについて',
        'settings_close_btn': '閉じる',
        'settings_lang_group': '言語',
        'accessibility_title': 'TuneRay — アクセシビリティ権限が必要です',
        'accessibility_msg': (
            'メディアキー（音量・再生）を制御するには「アクセシビリティ」権限が必要です。\n\n'
            'システム設定 → プライバシーとセキュリティ → アクセシビリティ\n'
            'で TuneRay（または Python）を許可してから、アプリを再起動してください。'
        ),
        'scan_confirm_title': 'デバイススキャン',
        'scan_confirm_msg': (
            'SONOSデバイスのスキャンには1〜2分かかる場合があります\n'
            '（マルチキャスト検索 → ARPホストスキャン）。\n\n実行しますか？'
        ),
        'scan_btn_scanning': '⏳ スキャン中...',
        'already_running': 'TuneRay はすでに起動しています。',
        'window_title': 'SONOS RAY イコライザーコントローラー Pro',
        'about_text': (
            '<b>SONOS RAY イコライザーコントローラー</b><br/><br/>'
            'PyQt6ベースのSONOS RAYスピーカー用イコライザーコントローラー<br/><br/>'
            '<b>機能:</b><ul>'
            '<li>Now Playing 表示（アルバムアート・曲名・アーティスト）</li>'
            '<li>再生コントロール（再生/一時停止・前後スキップ・ミュート・音量）</li>'
            '<li>AirPlay ストリーム対応（ミュートで代替）</li>'
            '<li>Bass / Treble / Volume 調整（macOS 互換ステップ）</li>'
            '<li>Loudness / Speech Enhancement / Night Sound トグル</li>'
            '<li>EQ プリセット管理（作成・編集・削除）</li>'
            '<li>複数デバイス管理（自動検出 + IPキャッシュ）</li>'
            '<li>メディアキーによるグローバルキーボード制御</li>'
            '</ul><b>必要環境:</b><ul>'
            '<li>Python 3.8+</li><li>PyQt6 / SoCo / pynput</li>'
            '<li>同一ネットワーク上のSONOSデバイス</li>'
            '</ul><b>License:</b> MIT'
        ),
        'state_on': 'ON',
        'state_off': 'OFF',
    },
}


def tr(key: str, **kwargs) -> str:
    text = _STRINGS.get(_LANG, _STRINGS['en']).get(key, key)
    return text.format(**kwargs) if kwargs else text


def set_language(lang: str):
    global _LANG, _app_settings
    _LANG = lang
    _app_settings['language'] = lang
    _save_app_settings(_app_settings)
