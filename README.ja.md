# Holographic Dreaming Plugin

[Hermes Agent](https://github.com/NousResearch/hermes-agent) 向けの、ポータブルな夜間メモリ整理パイプライン（"dreaming"）です。睡眠中に `MEMORY.md`、`USER.md`、holographic fact_store を整理します：セッションの事実とユーザーの修正を捕捉し、構造的に安全と証明できるものだけを照合し、水位に基づいてメモリを圧縮し、バックグラウンドで staged された書き換えを審査します。完全無人・fail-closed・成功時は無言です。

English: [README.md](README.md) ｜ 中文：[README.zh-CN.md](README.zh-CN.md)

## アーキテクチャ

```text
Hermes cron（ローカル配送、低コストモデル固定）
  → fact_extract_sweep（修正キャプチャ＋通常スイープ）
  → 修正の照合（構造的証明がある場合のみ適用、それ以外は内部 deferred）
  → pending staged 書き込みの審査（一件ずつ判定、適用または破棄）
  → MEMORY / USER の水位評価（閾値で定期スリム化）
  → 保護セット検証、操作ごとのレシート
```

判断はモデル層に残し、スクリプトは決定的な検証・実行・レシートを担当します。owner のアクションが不要な成功ランは stdout もプッシュ通知もゼロです。

## 5 ステップ・クイックスタート

1. holographic メモリ provider・memory ツール・cron が有効な Hermes インスタンスを用意。ランタイム Python が `tools.memory_tool` と `tools.write_approval` を import できること。
2. `HERMES_HOME` を設定。`scripts/` を `$HERMES_HOME/scripts/` に、skill を `$HERMES_HOME/skills/<category>/memory-consolidation/` に配置。
3. 対象インスタンスの保護セット EXPECTED を初期化。夜間書き込みを有効にする前に凍結ブロックを検証——空の EXPECTED がチェックを通過しても保護が存在する意味には**なりません**。
4. [docs/porting.md](docs/porting.md) に従って権限と水位を設定し、日次 cron を作成：`deliver=local`、低コストモデルを明示固定（例：DeepSeek flash 系）。
5. 初夜は隔離コピーで dry-run：操作ごとのレシート JSONL と保護チェックを検収し、プッシュがゼロであることを確認してから本番書き込みを有効化。

## 移植の要点

Hermes デプロイごとにツール API・承認ゲート・fact_store スキーマ・セッション DB・cron フィールドは異なります。一つずつマッピングし、他インスタンスの保護コンテンツは流用しないでください。完全なチェックリストは [docs/porting.md](docs/porting.md)、設計制約は [docs/design.md](docs/design.md)。

特にハマりやすい 3 点：

1. スクリプトは Hermes ランタイムの Python で実行すること（`tools.memory_tool` を import するため）。システム Python では動きません。
2. `memory.write_approval` はフォアグラウンド書き込みのみを制御します——バックグラウンドの破壊的 staging ゲートはランタイムコード内にあり、設定スイッチがありません。同梱の `memory_pending_review.py` がその承認を夜間フローに組み込みます。
3. `fact_extract_sweep.py` は外部の `session_fact_extract.py`（LLM 抽出チェーン）を必要とします。これは各デプロイ自身のモデル選択であり、意図的に同梱していません。

## 構成

- [cron/nightly-prompt.md](cron/nightly-prompt.md)：夜間ジョブのプロンプトテンプレート（パラメータ化済み）。
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md)：運用ルールと判断の境界。
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/)：rulings テンプレート、水位スリム化 SOP、pending 審査 SOP、判官キャリブレーション手法。
- [scripts/](scripts/)：セッション事実スイープ、共有状態、保護セットチェック、staged 書き込み審査。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
