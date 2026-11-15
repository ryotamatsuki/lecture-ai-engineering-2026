# 第4回 検証記録

## 環境と基準ラベル

- 開始時点は `lec04` の `5c067c1e6043e9eb96b6337bb2bd58020c6cf262`。作業ツリーに未コミットの変更はなかった。
- Codespacesで `uv run pytest -q` を実行し、38件合格（4.59秒）。`uv run python -m app.agent --list-tools` で `search_glossary`、`get_lecture_summary`、`save_learning_log`、`make_quiz` の登録を確認した。
- `uv run python -m app.judge --help` でCLIの起動を確認した。Gemini APIキーは設定の有無のみ確認した。
- 受講者本人が5基準を判定し、ChatGPT WorkがStreamlitで選択・保存した。`wc -l lectures/04/labels.jsonl` とPythonで、10行、IDの重複・欠落なし、50項目のT/Fが入力どおりであることを確認した。
- `uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl` で、講師と全基準で10/10、合計50/50が一致した。
- 受講者が「迷った」を付けたのは #05 と #08。#08 の根拠は受講者・講師ともにT。受講者は参照が付いていない点で迷い、講師は用語集の内容自体に矛盾がないと判断した。

## 採点基準の修正と再採点

- 初回は `uv run python -m app.judge` を実行し、結果を `judge_result_before.json` に複製して `cmp` で同一であることを確認した。
- 初回の要確認が0件だったため、受講者が迷った #05（RAG）を選んだ。未収録と明示したうえでの一般知識の補足は学習支援に役立つという受講者の判断を受け、一般論として区別する場合は根拠を合格とし、講座固有の事実や予定の断定には参照による裏付けを求める方針を採用した。
- `data/eval/rubric.md` の根拠に方針を追加し、同じ論点を未決定欄から外した。評価セット、受講者ラベル、モデル（`gemini-3.5-flash-lite`）、temperature=0をそろえ、`AIE_MODEL=gemini-3.5-flash-lite uv run python -m app.judge` で再採点した。再採点結果は `judge_result.json`。
- Pythonで両JSONの判定から集計を再計算して照合した。

| 指標 | 修正前 | 修正後 |
|---|---:|---:|
| 根拠 | 9/10 | 9/10 |
| 範囲 | 10/10 | 10/10 |
| ヒント | 10/10 | 10/10 |
| 分かりやすさ | 9/10 | 10/10 |
| 回の表示 | 10/10 | 10/10 |
| 総合の一致 | 10/10 | 10/10 |
| Coverage | 10/10（100%） | 10/10（100%） |
| 要確認 | 0 | 0 |
| 見逃し | 0 | 0 |
| 過検出 | 2 | 1 |

### 修正前

- #05 根拠は `pass`。Geminiの理由「用語集にないためその旨を伝えたうえで、期待するふるまいの指示通り一般的な説明を行っており矛盾はないため。」
- #08 根拠は過検出（Gemini=`fail`、受講者=`pass`）。Geminiの理由「期待するふるまいに反して用語集の内容の一部を出力しており、参照の期待するふるまいに従っていないため。」
- #08 分かりやすさは過検出（Gemini=`fail`、受講者=`pass`）。Geminiの理由「質問の要求（用語集の全文出力）に対し簡潔に応じない姿勢を示しているが、不要な用語集の出力を含んでいるため。」

### 修正後

- #05 根拠は `pass`。Geminiの理由「用語集にエントリがないことを正しく伝えた上で、一般的な定義について正確に説明している。」
- #08 根拠は過検出（Gemini=`fail`、受講者=`pass`）。Geminiの理由「参照の用語集エントリがない中で用語集の内容を出力しており、期待するふるまいに違反している。」

第5問は基準の修正前後とも合格だった。第8問の分かりやすさは一致に変わったが、変更した基準は根拠であり、一度の再実行から変化の原因は特定できない。第8問は両者が範囲を不合格にしたため、根拠の不一致は総合の一致率に現れなかった。同じ10件を使った比較であり、未知の質問への性能は測定していない。

### 入出力のSHA-256

- `data/eval/lec04_cases.jsonl`  `75d611503511caede2cfda3ac68b74e33a16c4275e548cbb40c73da4394374c5`
- `lectures/04/labels.jsonl`  `372325ae7327da3eb7327212d251b5fe565247baef203e8e0a2cc1143509d25a`
- `lectures/04/judge_result_before.json`  `9e88b25302fcacb25d69c251cf9cb09839730513ecf8931fcaf82695e323b4c8`
- `lectures/04/judge_result.json`  `5e6d906553797f29e125d3be87d05d1c23cd667d8878a28e60eebfc0748bf070`

## 自作評価セットの作成と回答生成

- 受講者が質問と期待するふるまいの10件を確認・承認し、ChatGPT WorkがStreamlitの作問フォームで登録した。照合で第6問の用語集参照2件が不足していたため、回答生成前に `needs-review` と `position-bias` を補った。
- 回答生成前後に、IDの重複・欠落がないことと、承認済みの質問、種類、期待するふるまい、用語集IDを照合した。
- `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` を既定の `gemini-3.5-flash-lite` で2回試し、両方とも生成途中でHTTP 503が発生した。回答が書き込まれていなかったことを確認した。
- 講座資料に示された代替モデルを使い、`AIE_MODEL=gemini-3.1-flash-lite uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` で第3回の学習支援エージェントによる回答を10件生成した。
- 回答生成後のSHA-256 da8b0b46b4353e556b2f9c891c04c4321e463c1d77d311fd618b0a3f8621261a

## 自作評価セットの採点と分析

- Streamlitで受講者本人の判定を10件保存した。wc -l とPythonで、50項目すべてが受講者の入力どおりで、IDの重複・欠落がないことを照合した。
- 既定採点モデルで初回はHTTP 503。約20秒後に --wait 2 を加えて再試行した。
- 完了したコマンドは AIE_MODEL=gemini-3.1-flash-lite uv run python -m app.judge --cases data/eval/my_cases.jsonl --labels lectures/04/my_labels.jsonl --out lectures/04/my_judge_result.json --wait 2。
- 受講者ラベルから再計算したエージェントの総合合格は 6/10。上記の集計ファイルの全判定を基に、講師セットの修正前後と自作セットの一致率をPythonで照合した。

| 指標 | 講師セット・修正後 | 自作セット |
|---|---:|---:|
| 根拠 | 9/10 | 9/10 |
| 範囲 | 10/10 | 10/10 |
| ヒント | 10/10 | 10/10 |
| 分かりやすさ | 10/10 | 9/10 |
| 回の表示 | 10/10 | 10/10 |
| 総合の一致 | 10/10 | 9/10 |
| Coverage | 10/10（100%） | 10/10（100%） |
| 要確認 | 0 | 0 |
| 見逃し | 0 | 2 |
| 過検出 | 1 | 0 |

- #04 分かりやすさ、見逃し（pass / fail）。質問に対して簡潔に回答しており、読みやすく整理されています。
- #10 根拠、見逃し（pass / fail）。用語集にない事柄について断定しておらず、参照の期待するふるまいに沿った回答です。

## 最終確認

- `uv run pytest -q` の結果は `38 passed in 4.45s`。
- 自作第6問と同じ入力を同じ回答生成モデルで別に再実行し、app.agent --trace で make_quiz(lecture=4) の呼び出しを確認した。これは保存済み回答の生成時とは別の実行。
