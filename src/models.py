"""
TuneRay — データモデル

フレームワーク非依存。Qt・Tk どちらからでも import 可能。
"""

import json
import os
from typing import List

from strings import _DATA_DIR

DEVICE_CACHE_PATH = os.path.join(_DATA_DIR, 'devices.json')
PRESETS_PATH = os.path.join(_DATA_DIR, 'presets.json')

_DEFAULT_PRESET_DATA = [
    {"name": "Clear",        "bass":  0, "treble":  5, "loudness": True,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Bass Boost",   "bass":  5, "treble":  0, "loudness": True,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Treble Boost", "bass":  0, "treble":  5, "loudness": False,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Neutral",      "bass":  0, "treble":  0, "loudness": False,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Warm",         "bass":  3, "treble": -2, "loudness": True,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Bright",       "bass": -2, "treble":  5, "loudness": False,
        "speech_enhancement": False, "night_mode": False},
    {"name": "Night",        "bass":  0, "treble":  0, "loudness": False,
        "speech_enhancement": True,  "night_mode": True},
]


class EQPreset:
    """EQ設定プリセット"""

    def __init__(self, name: str, bass: int, treble: int, loudness: bool,
                 speech_enhancement: bool = False, night_mode: bool = False):
        self.name = name
        self.bass = bass
        self.treble = treble
        self.loudness = loudness
        self.speech_enhancement = speech_enhancement
        self.night_mode = night_mode

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'bass': self.bass,
            'treble': self.treble,
            'loudness': self.loudness,
            'speech_enhancement': self.speech_enhancement,
            'night_mode': self.night_mode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'EQPreset':
        return cls(
            name=d['name'],
            bass=d['bass'],
            treble=d['treble'],
            loudness=d['loudness'],
            speech_enhancement=d.get('speech_enhancement', False),
            night_mode=d.get('night_mode', False),
        )


def load_presets() -> List[EQPreset]:
    try:
        if os.path.exists(PRESETS_PATH):
            with open(PRESETS_PATH, 'r', encoding='utf-8') as f:
                return [EQPreset.from_dict(d) for d in json.load(f)]
    except Exception:
        pass
    presets = [EQPreset.from_dict(d) for d in _DEFAULT_PRESET_DATA]
    save_presets(presets)
    return presets


def save_presets(presets: List[EQPreset]):
    try:
        with open(PRESETS_PATH, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in presets],
                      f, indent=2, ensure_ascii=False)
    except Exception:
        pass
