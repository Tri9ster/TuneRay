# TuneRay — Claude向けプロジェクトメモ

## 設計方針

### 外部アプリ制御禁止
Apple Music・Spotify等、特定の再生アプリへの制御は一切行わない。AppleScript（osascript）による操作も含む。
AirPlay・光デジタル入力時にメディアキーを押した場合はステータスバーにメッセージを表示するだけにとどめる。

### pynput `suppress=True` 使用禁止
pynput の `Listener(suppress=True)` を使用してはならない。
suppress=True にすると CGEventTap で全キーボードイベントを消費するため、アプリ起動中は他のアプリでキーボード入力が一切できなくなる（2025-05-05 実害確認）。
メディアキーのリスナーは常に `suppress=False` で起動する。

## 未解決課題

### メディアキーの選択的抑制（将来課題）
play/pause キーを押すと Apple Music が起動する問題が未解決。
pynput の設計上「メディアキーだけ抑制・他のキーは通す」という細かい制御ができない。
将来対応する場合は macOS の低レベルAPI（PyObjC の `NSEvent` / CGEventTap）を直接使う実装を検討する。現状は `suppress=False` で運用。
