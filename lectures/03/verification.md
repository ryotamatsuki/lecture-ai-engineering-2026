# 第3回 検証記録

実施日：2026年11月9日（日本時間）
実行場所：既存Codespaces paranormal zombieのVS Code Webのbashターミナル。
ブラウザからコマンドを入力し、Enterで実行し、標準出力・標準エラーを確認した。

## 開始状態

- ディレクトリ：/workspaces/lecture-ai-engineering-2026
- ブランチ：lec03
- 開始SHA：662cddd52724b330f3f4cd15123d1e55cb474874
- 開始時の未コミット変更：なし
- origin：ryotamatsuki/lecture-ai-engineering-2026
- upstream：matsuolab/lecture-ai-engineering-2026
- git pull --ff-only origin lec03で既存の保存・承認実装（4ad502592ff3f6472c665cef37146380bc6833a1）を取り込んだ。
- main・lec01・lec02の更新、強制push、履歴の書き換え、リセットは行っていない。
- rgが利用できなかったため、追加のAGENTS.md確認にはfindを使用した。

## 実行コマンド

```bash
pwd
git status --short --branch
git branch --show-current
git remote -v
git log -1 --oneline
git rev-parse HEAD
git pull --ff-only origin lec03
uv sync --frozen
uv run pytest -q
uv run python -m app.agent --list-tools
uv run python -m app.ask "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
uv run python -m app.agent --trace "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"
uv run python -m app.agent --trace "第2回の内容から確認問題を1問出して"
uv run python -m app.agent --trace "今日、LoRAは低ランク行列を利用したファインチューニング手法だと学んだ。この内容を学習記録に保存して"
git status --short
git diff --check
git diff --stat
```

実モデルの各出力は一時的にリポジトリ外の/tmp内へteeで保存して確認した。
保存質問は初回の指示調整用、承認用、拒否用に実行した。
承認用では表示内容を確認してからy、拒否用ではnを実際に入力した。
APIキーはGEMINI_API_KEYの有無だけを確認し、configuredだった。値の表示・記録・コミットは行っていない。
試験中は表示を簡潔にするためPYDANTIC_AI_NO_BANNER=1を設定した。

## テスト

uv sync --frozenは成功。依存バージョンとuv.lockは変更していない。
pytest結果：33 passed in 4.44s、失敗0件。
ツール一覧でsearch_glossary・get_lecture_summary・save_learning_log・make_quizの4件を確認した。

TestModelは実LLMを呼ばないテストとして使用した。
make_quizは用語集に収録された各講義回と、0・-1・99の回を検証した。
既存の承認・拒否・日本語保存・上書き防止テストも通過した。

## Gemini実モデルの実測

モデル：gemini-3.5-flash-lite。以下はTestModelの出力ではない。

| 実行 | ツール呼び出し | requests | 観察結果 |
|---|---|---|---|
| 通常のLLM | なし | このコマンドでは未表示 | 一般的な3段階を説明し、レベル2を目指すのが標準という推測を含んだ。 |
| エージェント・3レベル | search_glossary(query="3レベル") | 2 | 基礎・実装・発展、どれか1つで完了、原則採点なし、第1回と回答。 |
| LoRA/QLoRA | search_glossary(query="LoRA"), search_glossary(query="QLoRA") | 2 | LoRAと量子化併用のQLoRAの違いを説明し、第2回を記載。 |
| 第2回の確認問題 | make_quiz(lecture=2) | 2 | 量子化の意味を問う問題を生成。ツールはquestionとanswerを返し、最終回答は問題だけを提示。 |
| 保存・承認 | save_learning_log(topic="LoRA", content=承認画面の内容) | 1（再開後） | y入力後に保存され、最終回答も保存完了を伝えた。 |
| 保存・拒否 | save_learning_log(topic="LoRA", content=承認画面の内容) | 1（再開後） | n入力後にツール結果が拒否となり、最終回答も保存していないと説明。 |

保存時のrequestsは現在のCLIが表示した再開後の区間の値で、初回の保存要求生成まで含む総数ではない。
既存の--traceはツール返却内容を先頭120文字に省略するため、保存内容一致の確認には承認画面のJSONと保存JSONを使った。

## 保存の副作用を独立に確認

- 承認前：JSON 0件。承認待ちプロンプトを検出してから、承認前のファイル集合・ハッシュが不変であることをPythonでassertした。
- 承認後：JSON 1件。承認画面のtopic・contentをJSONとして読み取り、新しい保存ファイルの同じフィールドと一致することをassertした。
- 拒否前後：JSON 1件から1件。すべてのファイル名・SHA-256が一致することをassertした。
- 拒否の最終回答：「記録の保存は行われていません」。未保存なのに保存済みとは回答しなかった。
- 学習記録本体、長い生ログ、秘密情報は提出ファイルに含めない。

## 調整と制約

初回の保存依頼では、モデルがsearch_glossaryだけを呼び、自然言語で保存許可を尋ねて終了した。
保存時はまずsave_learning_logを呼び、CLIが承認を扱うよう指示文を改善した後、同じ保存依頼で承認・拒否の双方を検証した。
APIエラーやレート制限による未実施項目はなかった。
単発の実モデル試験であり、あらゆる入力でのツール選択を保証する評価ではない。
