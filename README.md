# TuneRay — SONOS EQ Controller

A Python GUI application for intuitive control of SONOS RAY speaker equalizer settings via the macOS menu bar.

SONOS RAY スピーカーのイコライザー設定を macOS メニューバーから直感的に操作する Python GUI アプリケーション。

---

## Highlight Feature / 目玉機能

### Control SONOS RAY over Optical Audio Input / 光デジタル入力時もフル制御

**SONOS RAY** では、AirPlay や Spotify Connect などの Wi-Fi 再生と異なり、**光デジタル（Toslink）入力**では通常アプリからの音量・EQ 操作ができません。

With **SONOS RAY**, volume and EQ are normally inaccessible from any app when audio is fed via **optical digital (Toslink) input** rather than AirPlay or Spotify Connect.

TuneRay はこの制限を回避します。下記の「光デジタル → AUX 変換アダプタ」を経由することで、**光デジタル接続中でも音量・Bass/Treble/ラウドネスをリアルタイムに調整**できます。

TuneRay works around this limitation. By routing audio through the adapter below, you can **adjust volume, Bass, Treble, and Loudness in real time — even during optical input**.

> **推奨アダプタ / Recommended Adapter**
>
> [Bluetooth トランスミッター / 光デジタル変換アダプタ (Amazon)](https://amzn.to/4adcL4p)

**接続構成 / Connection diagram:**

```
テレビ / TV
  └─[光デジタル Toslink]─▶ 変換アダプタ ─▶ SONOS RAY (AUX入力)
                                              ↑
                                      TuneRay が Wi-Fi 経由で
                                      音量・EQ を制御
                                      TuneRay controls volume
                                      & EQ over Wi-Fi
```

> **Note:** Album art and track info require the SONOS device to be connected via Wi-Fi.  
> **注意:** アルバムアートと再生情報の表示には、SONOS RAY の Wi-Fi 接続が必要です。

---

## Features / 機能

- **Equalizer** — Bass & Treble ±10 adjustment / Bass・Treble を±10の範囲で調整
- **Audio options** — Loudness, Speech Enhancement, Night Mode, Crossfade / ラウドネス・スピーチエンハンスメント・ナイトモード・クロスフェード
- **Playback control** — Play/Pause, Previous/Next, Shuffle, Repeat, Mute / 再生制御ボタン一式
- **Volume HUD** — macOS-style overlay on volume change / 音量変更時のオーバーレイ表示
- **Presets** — Built-in and custom EQ presets / 内蔵プリセット＋カスタムプリセット
- **Auto-discovery** — Finds SONOS devices on the network (multicast + ARP fallback) / ネットワーク上のデバイスを自動検出
- **Device cache** — Remembers the last-used device / 前回使用デバイスを記憶
- **Multilingual** — Japanese / English (switchable in settings) / 日本語・英語切り替え対応

---

## Requirements / 動作環境

| Item     | Detail                                    |
| -------- | ----------------------------------------- |
| OS       | macOS (recommended / 推奨)                |
| Python   | 3.8+                                      |
| Hardware | SONOS RAY (or any SoCo-compatible device) |

---

## Installation / インストール

```bash
pip install PyQt6 soco pynput
```

> **macOS note / macOS 注意**: The app requests Accessibility permission on first launch (required for media key support).
> 初回起動時にアクセシビリティ権限のリクエストが表示されます（メディアキー制御に必要）。

---

## Usage / 使い方

```bash
python sonos_eq_gui_advanced.py
```

1. The app appears as a **menu bar icon** (▶). Click it to open/close the panel.アプリは**メニューバーアイコン**（▶）として表示されます。クリックでパネルを開閉。
2. On first run, SONOS devices are discovered automatically. Results are cached for subsequent launches.初回起動時はデバイスを自動検出し、次回以降はキャッシュを使用します。
3. Adjust sliders, toggle checkboxes, apply presets, or use media keys.
   スライダー・チェックボックス・プリセット・メディアキーで操作できます。

---

## File Structure / ファイル構成

```
TuneRay/
├── sonos_eq_gui_advanced.py   # Entry point — Qt GUI main window / エントリーポイント
├── src/
│   ├── controller.py          # SonosEQController (framework-agnostic) / フレームワーク非依存コントローラー
│   ├── models.py              # Data models & preset persistence / データモデル・プリセット管理
│   ├── strings.py             # Multilingual UI strings / 多言語UI文字列
│   └── TuneRay.icns           # App icon / アプリアイコン
├── assets/
│   └── icon/                  # Source icon assets / アイコン素材
├── TuneRay.spec               # PyInstaller build spec / ビルド設定
└── README.md
```

---

## Design Principles / 設計方針

### No external app control / 外部アプリ制御禁止

The app only controls the SONOS device itself. It never launches or controls Apple Music, Spotify, or other players (no AppleScript).
Apple Music・Spotify 等の外部アプリへの制御は一切行いません（AppleScript も使用しません）。
Pressing media keys while an AirPlay or optical-input stream is active only shows a status message.
AirPlay・光デジタル入力中にメディアキーを押した場合はステータスバーにメッセージを表示するだけです。

### Keyboard listener safety / キーボードリスナーの安全性

`pynput` is always started with `suppress=False` to avoid blocking keyboard input in other apps.
他アプリのキーボード入力を妨げないよう、常に `suppress=False` で起動します。

### Framework-agnostic core / フレームワーク非依存なコア

`src/controller.py` and `src/models.py` have no dependency on PyQt6, making it straightforward to swap the GUI layer.
`src/controller.py` と `src/models.py` は PyQt6 に依存しないため、GUI フレームワークの変更が容易です。

---

## Troubleshooting / トラブルシューティング

### Device not found / デバイスが見つからない

- Ensure the device and Mac are on the same Wi-Fi network. / デバイスと Mac が同じ Wi-Fi ネットワーク上にあることを確認してください。
- Confirm the device is visible in the official SONOS app. / SONOS 公式アプリで認識されているか確認してください。
- Check firewall settings (UDP 1900 for SSDP). / ファイアウォール設定（SSDP: UDP 1900）を確認してください。

### Settings not applied / 設定が反映されない

- Check the SONOS RAY power status. / SONOS RAY の電源状態を確認してください。
- Re-select the device or press **Refresh** in Settings. / デバイスを再選択するか、設定画面の **更新** を押してください。

### Accessibility permission / アクセシビリティ権限

- Go to **System Settings → Privacy & Security → Accessibility** and enable TuneRay. / **システム設定 → プライバシーとセキュリティ → アクセシビリティ** で TuneRay を許可してください。

### "Apple cannot verify..." warning / 「Appleはマルウェアが含まれていないことを検証できませんでした」

TuneRay is not notarized with Apple, so macOS Gatekeeper may block the app on first launch.  
TuneRay は Apple の公証を受けていないため、初回起動時に Gatekeeper の警告が表示されることがあります。

**Option 1 — System Settings / システム設定から許可（推奨）:**

1. Double-click `TuneRay.app` once (dismiss the warning). / `TuneRay.app` を一度ダブルクリックして警告を閉じる。
2. Open **System Settings → Privacy & Security**. / **システム設定 → プライバシーとセキュリティ** を開く。
3. Scroll down to find the message about TuneRay and click **"Open Anyway"**. / 下部に表示される TuneRay に関するメッセージの横の **「このまま開く」** をクリック。
4. Double-click `TuneRay.app` again to launch. / もう一度 `TuneRay.app` をダブルクリックして起動。

**Option 2 — Terminal / ターミナルで解除:**

```bash
xattr -dr com.apple.quarantine /path/to/TuneRay.app
```

---

## License / ライセンス

MIT License

---

## References / 参考資料

- [SoCo — Python SONOS Controller](https://github.com/SoCo/SoCo)
- [SONOS Developer Portal](https://developer.sonos.com/)
