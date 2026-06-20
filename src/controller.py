"""
TuneRay — SONOS EQ コントローラー

フレームワーク非依存。Qt・Tk どちらからでも import 可能。
"""

from typing import Optional

from soco import SoCo, discover
from soco.exceptions import SoCoException


class SonosEQController:
    """SONOS RAYのイコライザー制御クラス"""

    def __init__(self, ip_address: Optional[str] = None):
        try:
            if ip_address:
                self.device = SoCo(ip_address)
                _ = self.device.player_name
            else:
                devices = list(discover())
                if not devices:
                    raise Exception("No Sonos devices found on the network")
                self.device = devices[0]
        except SoCoException as e:
            raise Exception(f"Failed to connect to Sonos device: {e}")

    def set_bass(self, value: int) -> bool:
        if not -10 <= value <= 10:
            raise ValueError("Bass value must be between -10 and 10")
        try:
            self.device.bass = value
            return True
        except SoCoException as e:
            raise Exception(f"Error setting bass: {e}")

    def get_bass(self) -> Optional[int]:
        try:
            return self.device.bass
        except SoCoException as e:
            raise Exception(f"Error getting bass: {e}")

    def set_treble(self, value: int) -> bool:
        if not -10 <= value <= 10:
            raise ValueError("Treble value must be between -10 and 10")
        try:
            self.device.treble = value
            return True
        except SoCoException as e:
            raise Exception(f"Error setting treble: {e}")

    def get_treble(self) -> Optional[int]:
        try:
            return self.device.treble
        except SoCoException as e:
            raise Exception(f"Error getting treble: {e}")

    def set_loudness(self, enabled: bool) -> bool:
        try:
            self.device.loudness = enabled
            return True
        except SoCoException as e:
            raise Exception(f"Error setting loudness: {e}")

    def get_loudness(self) -> Optional[bool]:
        try:
            return self.device.loudness
        except SoCoException as e:
            raise Exception(f"Error getting loudness: {e}")

    def set_speech_enhancement(self, enabled: bool) -> bool:
        try:
            self.device.dialog_mode = enabled
            return True
        except SoCoException as e:
            raise Exception(f"Error setting speech enhancement: {e}")

    def get_speech_enhancement(self) -> Optional[bool]:
        try:
            return self.device.dialog_mode
        except SoCoException as e:
            raise Exception(f"Error getting speech enhancement: {e}")

    def set_night_mode(self, enabled: bool) -> bool:
        try:
            self.device.night_mode = enabled
            return True
        except SoCoException as e:
            raise Exception(f"Error setting night mode: {e}")

    def get_night_mode(self) -> Optional[bool]:
        try:
            return self.device.night_mode
        except SoCoException as e:
            raise Exception(f"Error getting night mode: {e}")

    def set_volume(self, value: int) -> bool:
        if not 0 <= value <= 100:
            raise ValueError("Volume must be between 0 and 100")
        try:
            self.device.volume = value
            return True
        except SoCoException as e:
            raise Exception(f"Error setting volume: {e}")

    def get_volume(self) -> Optional[int]:
        try:
            return self.device.volume
        except SoCoException as e:
            raise Exception(f"Error getting volume: {e}")

    @property
    def _coordinator(self) -> 'SoCo':
        """再生制御はグループのコーディネーターに送る必要がある"""
        try:
            coord = self.device.group.coordinator
            return coord if coord else self.device
        except Exception:
            return self.device

    def is_playing(self) -> bool:
        try:
            info = self._coordinator.get_current_transport_info()
            return info.get('current_transport_state') == 'PLAYING'
        except Exception:
            return False

    def play(self) -> bool:
        try:
            self._coordinator.play()
            return True
        except Exception as e:
            raise Exception(f"Error playing: {e}")

    def pause(self) -> bool:
        try:
            self._coordinator.pause()
            return True
        except Exception as e:
            raise Exception(f"Error pausing: {e}")

    def next_track(self) -> bool:
        try:
            self._coordinator.next()
            return True
        except Exception as e:
            raise Exception(f"Error skipping track: {e}")

    def previous_track(self) -> bool:
        try:
            self._coordinator.previous()
            return True
        except Exception as e:
            raise Exception(f"Error rewinding track: {e}")

    def get_mute(self) -> bool:
        try:
            return self.device.mute
        except SoCoException as e:
            raise Exception(f"Error getting mute: {e}")

    def set_mute(self, muted: bool) -> bool:
        try:
            self.device.mute = muted
            return True
        except SoCoException as e:
            raise Exception(f"Error setting mute: {e}")

    # URI プレフィックスが一致する場合は再生制御不可
    _UNCONTROLLABLE_PREFIXES = (
        'x-sonos-htastream:',  # TV音声 (HDMI ARC / 光デジタル)
        'x-rincon-stream:',    # ライン入力
    )

    def get_current_track_info(self) -> dict:
        try:
            info = self._coordinator.get_current_track_info()
            transport = self._coordinator.get_current_transport_info()
            info['_transport_state'] = transport.get(
                'current_transport_state', '')
            uri = info.get('uri', '')
            info['_controllable'] = not uri.startswith(
                self._UNCONTROLLABLE_PREFIXES)
            info['_muted'] = self.device.mute
            return info
        except SoCoException as e:
            raise Exception(f"Error getting track info: {e}")

    # ── クロスフェード ──────────────────────────────────────────────────────────

    def get_cross_fade(self) -> bool:
        try:
            return bool(self._coordinator.cross_fade)
        except Exception as e:
            raise Exception(f"Error getting cross_fade: {e}")

    def set_cross_fade(self, enabled: bool) -> bool:
        try:
            self._coordinator.cross_fade = enabled
            return True
        except Exception as e:
            raise Exception(f"Error setting cross_fade: {e}")

    # ── シャッフル / リピート ───────────────────────────────────────────────────
    # SoCo の play_mode は 'NORMAL' / 'SHUFFLE_NOREPEAT' / 'SHUFFLE' /
    # 'REPEAT_ALL' / 'REPEAT_ONE' / 'SHUFFLE_REPEAT_ONE' の組み合わせ文字列。
    # shuffle と repeat を独立して操作するため、現在の play_mode を読んで
    # 一方だけ変えて書き戻す。

    _PLAY_MODE_TABLE = {
        (False, 'off'):  'NORMAL',
        (True,  'off'):  'SHUFFLE_NOREPEAT',
        (False, 'all'):  'REPEAT_ALL',
        (True,  'all'):  'SHUFFLE',
        (False, 'one'):  'REPEAT_ONE',
        (True,  'one'):  'SHUFFLE_REPEAT_ONE',
    }
    _PLAY_MODE_PARSE = {v: k for k, v in _PLAY_MODE_TABLE.items()}

    def _get_play_mode_parts(self) -> tuple:
        """(shuffle: bool, repeat: str) を返す。repeat は 'off'/'all'/'one'"""
        raw = self._coordinator.play_mode.upper()
        return self._PLAY_MODE_PARSE.get(raw, (False, 'off'))

    def get_shuffle(self) -> bool:
        try:
            return self._get_play_mode_parts()[0]
        except Exception as e:
            raise Exception(f"Error getting shuffle: {e}")

    def set_shuffle(self, enabled: bool) -> bool:
        try:
            _, repeat = self._get_play_mode_parts()
            self._coordinator.play_mode = self._PLAY_MODE_TABLE[(enabled, repeat)]
            return True
        except Exception as e:
            raise Exception(f"Error setting shuffle: {e}")

    def get_repeat(self) -> str:
        """'off' / 'all' / 'one' を返す"""
        try:
            return self._get_play_mode_parts()[1]
        except Exception as e:
            raise Exception(f"Error getting repeat: {e}")

    def set_repeat(self, mode: str) -> bool:
        """mode: 'off' / 'all' / 'one'"""
        try:
            shuffle, _ = self._get_play_mode_parts()
            self._coordinator.play_mode = self._PLAY_MODE_TABLE[(shuffle, mode)]
            return True
        except Exception as e:
            raise Exception(f"Error setting repeat: {e}")

    # ── ステータスライト ────────────────────────────────────────────────────────

    def get_status_light(self) -> bool:
        try:
            return bool(self.device.status_light)
        except Exception as e:
            raise Exception(f"Error getting status_light: {e}")

    def set_status_light(self, enabled: bool) -> bool:
        try:
            self.device.status_light = enabled
            return True
        except Exception as e:
            raise Exception(f"Error setting status_light: {e}")

    def get_all_eq_settings(self) -> dict:
        def safe(fn):
            try:
                return fn()
            except Exception:
                return None

        return {
            'bass':               safe(lambda: self.device.bass),
            'treble':             safe(lambda: self.device.treble),
            'loudness':           safe(lambda: self.device.loudness),
            'speech_enhancement': safe(lambda: self.device.dialog_mode),
            'night_mode':         safe(lambda: self.device.night_mode),
            'volume':             safe(lambda: self.device.volume),
            'cross_fade':         safe(lambda: bool(self._coordinator.cross_fade)),
            'shuffle':            safe(lambda: self._get_play_mode_parts()[0]),
            'repeat':             safe(lambda: self._get_play_mode_parts()[1]),
            'status_light':       safe(lambda: bool(self.device.status_light)),
            'device_name':        safe(lambda: self.device.player_name) or 'Unknown',
            'ip_address':         safe(lambda: self.device.ip_address) or '',
        }
