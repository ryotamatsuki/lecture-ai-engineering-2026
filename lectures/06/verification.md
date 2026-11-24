# 第6回 検証記録

実施日：2026年11月24日（日本時間）。GitHub Codespaces の既存環境で実行した。AI が操作、公式資料の調査、ログの照合と記録を担当した。本書の確認結果は実行ログや参照資料に基づく。

## 準備

- 開始時のブランチは `lec04`（`origin/lec04` を追跡）。`git status --short --branch` に変更ファイルは表示されなかった。
- `origin` は自分の fork、`upstream` は松尾・岩澤研究室の公式リポジトリ。フォークの `main` は `662cddd` で、`lec05` と `lec06` のリモートブランチは確認できなかった。第5回の個別課題ブランチを前提にせず、公式の `lec06-start` を使用した。前回までの独自実装は既存ブランチで管理したまま、第6回では教材のエージェントを使った。
- `git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec06-start` と `git switch -c lec06 lec06-start` を実行した。教材の `app/mcp_agent.py` が存在し、`uv sync --frozen` は完了した。
- `GEMINI_API_KEY` は設定済み。端末では変数の有無だけを確認した。
- 起動直後にブラウザでネットワークエラーが出た。再接続で既存 Codespace の VS Code と bash を利用できた。

## STEP 1　モデルに渡るツール

`uv run python -m app.agent --list-tools` と `uv run python -m app.mcp_agent --list-tools` を実行し、両方で終了コード 0 を確認した。直接登録のツールと MCP で取得したツールの両方で、名前・説明・入力スキーマが表示された。MCP 側はサーバー名を先頭に付け、異なるサーバーにある同名のツールを区別する。

### 直接登録の表示

```text
モデルに見えているツール: 1 個

[search_materials]
  第1〜3回の本講義資料を検索し、関連ページの本文・タイトル・ページ番号を返す。

  queryに調べたい内容を指定する。
  引数: {"query": {"type": "string"}}
```

### 用語集サーバーだけの場合

```text
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
モデルに見えているツール: 1 個

[glossary_search_glossary]
  講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

  AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
  答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
  引数: {"query": {"title": "Query", "type": "string"}}
```

## STEP 2〜4　Gemini での実行

| STEP | ツールの戻り値の確認 | エージェントの最終回答 |
| --- | --- | --- |
| 2 用語集 | `宿題の3レベル` の定義を取得した。 | 基礎は講義内容の確認、実装はコードの作成、発展は調査や試行と説明した。 |
| 3 fetch | MCP 公式サイトの本文がツールから返った。 | MCP を AI アプリと外部システムをつなぐオープンな標準と説明し、役割と利用範囲を含めて日本語3行にまとめた。 |
| 4 AWS Knowledge | S3 バージョニングに関する AWS 公式文書の検索結果を取得した。 | 同じバケット内のオブジェクトの複数世代を保持し、上書きや削除後の復元に使えると、日本語2行で説明した。 |

STEP 3 では `app/mcp_servers.json` に fetch を追加して一覧を取得し、`fetch_fetch` が増えたことを確認した。MCP プロジェクト提供の `mcp-server-fetch` が `uvx` 経由で Codespaces 内に起動する。指定版 `2026.11.11` に固定することで、パッケージ本体の更新に伴う動作の変化を避けた。`--no-readability-js` は Python のみで本文を抽出する指定。README では、非公開アドレスへの接続は既定で拒否し、モデルによるページ取得では `robots.txt` に従う。運用上さらに取得先を絞る場合には `--allowed-hosts` が使える。演習は既定の保護を有効にしたまま公開サイトを取得した。 [fetch README](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) · [公式リリース](https://github.com/modelcontextprotocol/servers/releases/tag/v2.4.0)

STEP 4 では AWS Knowledge の URL を追加して一覧を取得し、`aws_` で始まるツールを確認した。AWS が運用する公開サービスに Streamable HTTP で接続し、公開ドキュメントの検索に必要な引数を送った。AWS アカウントなしで利用でき、利用回数には制限がある。 [AWS 公式設定資料](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server) · [AWS 公式発表](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-knowledge-mcp-server-generally-available/)

各トレースは終了コード 0。この演習では代替モデルを使わなかった。`[tool return]` は講座の CLI が戻り値の先頭を表示したもので、以下では必要な部分を抜粋した。

### STEP 2

`uv run python -m app.mcp_agent --trace 'AIE2026の講座の宿題にある「3レベル」とは何ですか？'`

```text
[model] gemini-3.5-flash-lite
[tool call]   glossary_search_glossary({'query': '3レベル'})
[tool return] glossary_search_glossary -> [{"term": "宿題の3レベル", "lecture": 1, "definition": "AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組…
[usage] 入力 715 tokens / 出力 151 tokens / モデル応答 2 回
```

### STEP 3

`uv run python -m app.mcp_agent --list-tools` の出力（接続先とツール名）

```text
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
[server] fetch: コマンドで起動（uvx mcp-server-fetch==2026.11.11 --no-readability-js）
モデルに見えているツール: 2 個
[glossary_search_glossary]
[fetch_fetch]
```

`uv run python -m app.mcp_agent --trace 'https://modelcontextprotocol.io/ の冒頭を日本語で3行に要約して'`

```text
[model] gemini-3.5-flash-lite
[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
[tool return] fetch_fetch -> Contents of https://modelcontextprotocol.io/: …
[usage] 入力 2,179 tokens / 出力 115 tokens / モデル応答 2 回
```

### STEP 4

`uv run python -m app.mcp_agent --list-tools` の出力（接続先とツール名）

```text
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
[server] fetch: コマンドで起動（uvx mcp-server-fetch==2026.11.11 --no-readability-js）
[server] aws: URL に接続（https://knowledge-mcp.global.api.aws）
モデルに見えているツール: 7 個
[glossary_search_glossary]
[fetch_fetch]
[aws_aws___read_documentation]
[aws_aws___search_documentation]
[aws_aws___list_regions]
[aws_aws___get_regional_availability]
[aws_aws___retrieve_skill]
```

`uv run python -m app.mcp_agent --trace 'AWSのドキュメントを検索して、Amazon S3 のバージョニングを2行で説明して'`

```text
[model] gemini-3.5-flash-lite
[tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
[tool return] aws_aws___search_documentation -> {'content': {'result': [{'rank_order': 1, 'title': 'Amazon S3 FAQs', 'context': '#### What is Versioning?\n\nVersioning …
[usage] 入力 6,359 tokens / 出力 96 tokens / モデル応答 2 回
```

## 最終確認

- `uv run pytest -q`：初期 21 passed in 6.63s、変更後 21 passed in 4.15s。
- Python で、解答中の JSON が実際の設定と一致し、TOML にも同じ3件と起動・接続の設定があることを確認した。Codex の設定例は公式資料をもとに作成し、Codex からの接続試験は行っていない。
- `git diff --check` とステージ後の `git diff --cached --check` を通過し、今回の設定と文書の3ファイルを提出対象とした。認証情報の混入を確認する検査も通過した。
