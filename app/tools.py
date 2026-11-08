"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from random import choice
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def save_learning_log(topic: str, content: str) -> str:
    """利用者が学習内容の記録を依頼したとき、題名と内容を learning_log/ に保存する。

    topic は学習テーマ、content は記録する学習内容。保存前に利用者の承認が必要。
    単なる質問への回答では使わず、記録・保存を依頼されたときだけ使う。
    保存先とファイル名はプログラム側で決め、既存の記録は上書きしない。
    """
    now = datetime.now(timezone.utc)
    path = LEARNING_LOG_DIR / f"{now:%Y%m%dT%H%M%S%fZ}_{uuid4().hex}.json"
    record = {"created_at": now.isoformat(), "topic": topic, "content": content}
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return f"学習記録を保存しました: {path}"


def make_quiz(lecture: int) -> str:
    """指定した回の用語集から、用語の意味を問う復習問題を1問返す。

    「第2回から確認問題を出して」など、確認問題・クイズを求められたときに使う。
    lecture は1始まりの講義回（例: 2）。question と answer を含む JSON を返す。
    用語がない回では空の question・answer と案内 message を返す。
    """
    terms = [entry for entry in load_glossary() if entry["lecture"] == lecture]
    if not terms:
        return json.dumps(
            {"question": "", "answer": "", "message": f"第{lecture}回の用語はまだありません。"},
            ensure_ascii=False,
        )
    entry = choice(terms)
    return json.dumps(
        {"question": f"「{entry['term']}」とは何ですか？", "answer": entry["definition"]},
        ensure_ascii=False,
    )
