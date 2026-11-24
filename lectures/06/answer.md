# 第6回 解答

## 演習

- STEP 1 のツールの名前：直接登録は `search_materials`、MCP 経由は `glossary_search_glossary`。どちらも引数 `query` は文字列。

STEP 2 の実行ログ

```text
[tool call]   glossary_search_glossary({'query': '3レベル'})
```

STEP 3 の実行ログ

```text
[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
```

STEP 4 の実行ログ

```text
[tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
```

- 気づき・疑問：用語集は URL を必要とせず、ローカルで起動した MCP サーバーが検索を実行する。直接登録でも MCP 経由でも、ツール名・説明・入力スキーマがモデルに渡る。講座のクライアントは、MCP ツールを登録する際にサーバー名を接頭辞にして同名のツールを区別する。3件とも Gemini がツールの戻り値を受け取って回答する過程を確認できた。実行条件と結果の詳細は [verification.md](verification.md) に記録した。

## 宿題

- 取り組んだレベル：発展
- 調査対象：OpenAI Codex（CLI、IDE 拡張機能）
- 調査日：2026年11月24日
- やったこと：OpenAI の公式ドキュメントを読み、演習で使う3サーバーの設定を Codex 用の TOML に置き換えて比較した。Codex での設定変更や接続試験は行っていない。

### 講座と Codex の設定の比較

| 観点 | 講座のエージェント | OpenAI Codex |
| --- | --- | --- |
| 設定名と配置 | リポジトリの `app/mcp_servers.json` に `mcpServers` を置く。 | 既定はユーザーの `~/.codex/config.toml`。信頼済みプロジェクトには `.codex/config.toml` を置ける。各サーバーは `[mcp_servers.<名前>]` に記す。 |
| ローカル起動 | `command` と `args` でサブプロセスを起動し、標準入出力（stdio）で通信する。 | 同じく `command` と `args` を指定する。必要に応じて `cwd` も指定できる。 |
| リモート接続 | `url` に公開サーバーのエンドポイントを指定する。 | `url` で Streamable HTTP のエンドポイントを指定する。サーバーに応じて OAuth や環境変数の Bearer トークンを利用できる。 |
| 有効範囲 | このリポジトリの `app.mcp_agent` が読み込む。 | ユーザー設定は同じ Codex ホスト上で CLI と IDE 拡張機能が共有する。プロジェクト設定は信頼済みの作業ディレクトリに適用される。 |

Codex CLI では stdio の登録に `codex mcp add <名前> -- <コマンド> <引数>`、リモートの登録に `codex mcp add <名前> --url <URL>` を使える。OAuth 対応サーバーには `codex mcp login <名前>` がある。TOML の `bearer_token_env_var` にはトークンを入れる環境変数の名前を指定する。 `enabled_tools` は公開するツールの許可リスト、`disabled_tools` はその後に適用する除外リストである。

### 3種類の接続設定

| サーバー | 設定する起動コマンド・接続先 | 実行場所と通信方式 |
| --- | --- | --- |
| glossary | `uv run python -m app.mcp_server` | エージェント側で自作サーバーを起動し、stdio で接続 |
| fetch | `uvx mcp-server-fetch==2026.11.11 --no-readability-js` | エージェント側で公開パッケージを取得して起動し、stdio で接続 |
| AWS Knowledge | `https://knowledge-mcp.global.api.aws` | AWS の運用環境に Streamable HTTP で接続 |

講座の JSON（`app/mcp_servers.json`）

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
    },
    "aws": {
      "url": "https://knowledge-mcp.global.api.aws"
    }
  }
}
```

Codex の TOML（調査用の記述例）

```toml
[mcp_servers.glossary]
command = "uv"
args = ["run", "python", "-m", "app.mcp_server"]
cwd = "/path/to/lecture-ai-engineering-2026"

[mcp_servers.fetch]
command = "uvx"
args = ["mcp-server-fetch==2026.11.11", "--no-readability-js"]

[mcp_servers.aws]
url = "https://knowledge-mcp.global.api.aws"
```

`cwd` は Codex が動作するホスト上のリポジトリの絶対パスに置き換える。stdio の2例では同じホストから `uv` と `uvx` が実行できることが前提になる。

### 調査結果と気づき

- サーバーがツール名、説明、入力スキーマを MCP で提供し、クライアントが同じプロトコルで一覧取得と呼び出しを行うため、ツールの実装を共有できる。一方、設定ファイルの形式や範囲、モデルに見せるツール名、権限の扱いはクライアントに依存する。
- 日常のエージェント開発では、用語集の検索などを読み取り専用ツールとして切り出すと、講座のエージェントと開発支援クライアントで同じ検索処理を利用できる。ツールの説明と引数の型を明確にすると、接続先が増えた際にもモデルが用途を判断しやすい。
- リモートサービスにはツールの引数が送られるため、公開情報の検索に用途を絞り、認証が必要な場合は最小権限を設定する。ローカル起動でも、提供元と実行するバージョンを確認し、外部コンテンツの取得範囲やモデルに公開するツールを必要に応じて制限する。
- 今回の資料で分かったのは設定の対応関係である。異なるクライアントで同じツールを提示しても、モデルがいつ使うかは指示や質問に左右されるため、運用に移す場合は代表的な質問で呼び出しを確認したい。

### 参照した公式ドキュメント

- [OpenAI・Model Context Protocol](https://developers.openai.com/codex/mcp)
- [OpenAI・Config basics](https://developers.openai.com/codex/config-basic)
- [OpenAI・Configuration reference](https://developers.openai.com/codex/config-reference)
- [Model Context Protocol・fetch README](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- [AWS・AWS Knowledge MCP Server](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)
