# Hermes メモリスタック

Hermes Agent のメモリシステムを、そのまま別インスタンスへ持ち込める形にした二つの半分：**fact store バックエンド**（`holographic-plus` メモリ provider）と、**夜間の自動整理パイプライン**（dreaming）。どちらも単一ユーザーの本番デプロイから抽出し、パラメータ化したものです。

English: [README.md](README.md) ｜ 中文：[README.zh-CN.md](README.zh-CN.md)

## 同梱物

| 半分 | 内容 | 場所 |
| --- | --- | --- |
| **fact store** | SQLite ベースの構造化メモリ：facts / entities / 信頼スコア / HRR 合成検索 / 任意のセマンティック（embedding）検索。`fact_store`・`fact_feedback` ツールを公開し、ターンごとに検索結果を注入。 | [`plugin/holographic-plus/`](plugin/holographic-plus/) + [docs/factstore.md](docs/factstore.md) |
| **dreaming** | 無人で走る夜間ジョブ：セッションの事実とユーザー修正を捕捉し、構造的に安全と証明できる分だけ照合、水位に基づいて `MEMORY.md` / `USER.md` をスリム化、バックグラウンドで staged された書き換えを審査。fail-closed、成功時は無言。 | [`cron/`](cron/)、[`skills/`](skills/)、[`scripts/`](scripts/) + [docs/design.md](docs/design.md) |

二つは独立しています。夜間ジョブがなくても store は動き、夜間ジョブの store 関連ステップには store が必要です。Hermes には同じスキーマの `holographic` provider が同梱済みで、本リポジトリの fork はその上にセマンティック検索・セマンティックなエンティティ統合・CJK エンティティ抽出を追加します（[docs/holographic-plus.md](docs/holographic-plus.md)）。

## アーキテクチャ

```text
                    ┌─ fact_store(add)         ─┐
書き込み ───────────┼─ memory ツールのミラー     ─┼─→ memory_store.db  ── 読み手 ──→  システムプロンプトの状態ブロック
                    ├─ セッション終了 hook      ─┤     facts / entities /           ターンごとの prefetch
                    └─ 夜間 dreaming           ─┘     FTS5 / HRR banks /            search / probe / related /
                                                      embedding sidecar              reason / contradict
```

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

1. holographic メモリ provider（同梱の `holographic`、または本リポジトリの fork）・memory ツール・cron が有効な Hermes インスタンスを用意。ランタイム Python が `tools.memory_tool` と `tools.write_approval` を import できること。
2. `HERMES_HOME` を設定。`scripts/` を `$HERMES_HOME/scripts/`、skill を `$HERMES_HOME/skills/<category>/memory-consolidation/`、fork を使う場合は `plugin/holographic-plus/` を `$HERMES_HOME/plugins/` に配置。
3. 対象インスタンスの保護セット EXPECTED を初期化。夜間書き込みを有効にする前に凍結ブロックを検証——空の EXPECTED がチェックを通過しても保護が存在する意味には**なりません**。
4. [docs/porting.md](docs/porting.md) に従って権限と水位を設定し、日次 cron を作成：`deliver=local`、低コストモデルを明示固定（例：DeepSeek flash 系）。
5. 初夜は隔離コピーで dry-run：操作ごとのレシート JSONL と保護チェックを検収し、プッシュがゼロであることを確認してから本番書き込みを有効化。

## 移植の要点

Hermes デプロイごとにツール API・承認ゲート・fact_store スキーマ・セッション DB・cron フィールドは異なります。一つずつマッピングし、他インスタンスの保護コンテンツは流用しないでください。完全なチェックリストは [docs/porting.md](docs/porting.md)、設計制約は [docs/design.md](docs/design.md)。

特にハマりやすい 4 点：

1. スクリプトは Hermes ランタイムの Python で実行すること（`tools.memory_tool` と store を import するため）。システム Python では動きません。
2. `memory.write_approval` はフォアグラウンド書き込みのみを制御します——バックグラウンドの破壊的 staging ゲートはランタイムコード内にあり、設定スイッチがありません。同梱の `memory_pending_review.py` がその承認を夜間フローに組み込みます。
3. `fact_extract_sweep.py` は外部の `session_fact_extract.py`（LLM 抽出チェーン）を必要とします。これは各デプロイ自身のモデル選択であり、意図的に同梱していません——無い場合スイープは実質空回りになります。
4. `hrr_vector` を書くものは HRR 次元を**単一の**情報源（プラグイン設定）から読むこと。次元を自前でハードコードしたバイパススクリプトはストアを破壊します：次元不一致で書き込みが拒否されるか、異形 blob が黙って格納されます。

## 構成

- [plugin/holographic-plus/](plugin/holographic-plus/)：メモリ provider（同梱 `holographic` の fork）。
- [docs/factstore.md](docs/factstore.md)：fact store のデータモデル、読み書き経路、スコアリング、HRR、信頼スコア。
- [docs/holographic-plus.md](docs/holographic-plus.md)：fork の追加点、設定キー、導入/ロールバック、HRR 次元の規律。
- [cron/nightly-prompt.md](cron/nightly-prompt.md)：夜間ジョブのプロンプトテンプレート（パラメータ化済み）。
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md)：運用ルールと判断の境界。
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/)：rulings テンプレート、水位スリム化 SOP、pending 審査 SOP、判官キャリブレーション手法。
- [scripts/](scripts/)：セッション事実スイープ、共有状態、保護セットチェック、staged 書き込み審査。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。`plugin/` ディレクトリは Hermes Agent 同梱の `holographic` provider に由来します（MIT、© 2025 Nous Research、原作者 dusterbloom）——[plugin/holographic-plus/NOTICE](plugin/holographic-plus/NOTICE) を参照。
