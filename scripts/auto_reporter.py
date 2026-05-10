#!/usr/bin/env python3
"""
AtCoder ABC Auto Reporter
毎週土曜日のABCコンテストの提出を自動分析し、AI解説レポートを生成する。
"""

import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
ATCODER_PROBLEMS_API = "https://kenkoooo.com/atcoder"
USER = "uta516"
SCRAPE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AtCoderAutoReporter/1.0)"}


# ---------------------------------------------------------------------------
# データ取得
# ---------------------------------------------------------------------------

def get_todays_abc_contest() -> dict | None:
    """今日開催のABCコンテストを返す。見つからなければNone。"""
    resp = requests.get(f"{ATCODER_PROBLEMS_API}/resources/contests.json", timeout=30)
    resp.raise_for_status()
    today = datetime.now(JST).date()
    for contest in resp.json():
        if not contest["id"].startswith("abc"):
            continue
        start_dt = datetime.fromtimestamp(contest["start_epoch_second"], tz=JST)
        if start_dt.date() == today:
            return contest
    return None


def get_user_submissions(user: str, from_epoch: int) -> list[dict]:
    """指定エポック秒以降のユーザー提出をすべて返す。"""
    resp = requests.get(
        f"{ATCODER_PROBLEMS_API}/atcoder-api/v3/user/submissions",
        params={"user": user, "from_second": from_epoch},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def latest_per_problem(submissions: list[dict], contest_id: str) -> dict[str, dict]:
    """問題ごとの最新提出を返す（同一問題に複数回提出した場合は最新を採用）。"""
    contest_subs = [s for s in submissions if s["contest_id"] == contest_id]
    latest: dict[str, dict] = {}
    for sub in sorted(contest_subs, key=lambda x: x["epoch_second"]):
        latest[sub["problem_id"]] = sub
    return latest


def scrape_problem(contest_id: str, problem_id: str) -> dict:
    """AtCoderから問題タイトルと問題文を取得する。"""
    url = f"https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}"
    try:
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
        if resp.status_code != 200:
            return {"title": problem_id, "statement": "(問題文の取得に失敗しました)"}
        soup = BeautifulSoup(resp.text, "html.parser")
        title_elem = soup.find("span", class_="h2")
        title = title_elem.get_text(strip=True) if title_elem else problem_id
        task_div = soup.find("div", id="task-statement")
        statement = task_div.get_text(separator="\n", strip=True)[:4000] if task_div else ""
        return {"title": title, "statement": statement}
    except Exception as e:
        return {"title": problem_id, "statement": f"(取得エラー: {e})"}


def scrape_submission_code(contest_id: str, submission_id: int) -> str | None:
    """提出コードを取得する。ログイン不要で取得できない場合はNoneを返す。"""
    url = f"https://atcoder.jp/contests/{contest_id}/submissions/{submission_id}"
    try:
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        code_elem = soup.find("pre", id="submission-code")
        return code_elem.get_text() if code_elem else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# AI解説生成
# ---------------------------------------------------------------------------

def build_prompt(
    problem_title: str,
    problem_statement: str,
    result: str,
    source_code: str | None,
) -> tuple[str, str]:
    """(system, user) プロンプトを返す。"""
    code_block = (
        f"\n\n**提出コード:**\n```python\n{source_code}\n```" if source_code else ""
    )

    if result == "AC":
        system = (
            "あなたは競技プログラミングの専門家です。"
            "Pythonでの最適解とわかりやすいアルゴリズム解説を提供してください。"
        )
        user = f"""以下のAtCoder問題について解説してください。

問題: {problem_title}
提出結果: ✅ AC（正解）{code_block}

問題文:
{problem_statement}

---
以下の形式で回答してください:

## アルゴリズム解説
（何を求めているか・どの手法で解くかを簡潔に）

## 計算量
- 時間計算量: O(?)
- 空間計算量: O(?)

## Python 模範解答
```python
# 最適化されたコード
```

## 実装のポイント
（重要な注意点・落とし穴）
"""
    else:
        system = (
            "あなたは競技プログラミングの専門家です。"
            "不正解の原因を的確に分析し、正解への道筋を示してください。"
        )
        user = f"""以下のAtCoder問題について、提出が {result} になった原因を分析してください。

問題: {problem_title}
提出結果: ❌ {result}（不正解）{code_block}

問題文:
{problem_statement}

---
以下の形式で回答してください:

## {result} の原因分析
（エッジケースの漏れ・計算量の問題・アルゴリズムの誤りなどを具体的に）

## 正解アルゴリズム
（何を求めているか・どの手法で解くべきか）

## 計算量
- 時間計算量: O(?)
- 空間計算量: O(?)

## Python 正解模範解答
```python
# 正解コード
```

## 実装のポイント
（重要な注意点・落とし穴）
"""
    return system, user


def generate_ai_explanation(
    problem_title: str,
    problem_statement: str,
    result: str,
    source_code: str | None,
) -> str:
    """Google Gemini APIで解説を生成する。"""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.types.GenerationConfig(max_output_tokens=2000),
    )
    system, user = build_prompt(problem_title, problem_statement, result, source_code)
    # Gemini はシングルターン: system指示とuserメッセージを結合して送信
    full_prompt = f"{system}\n\n{user}"
    response = model.generate_content(full_prompt)
    return response.text


# ---------------------------------------------------------------------------
# レポート生成
# ---------------------------------------------------------------------------

def build_report(
    contest_id: str,
    contest_num: str,
    today: datetime,
    problem_results: list[dict],
) -> str:
    lines = [
        f"# {contest_id.upper()} 解法レポート\n",
        f"**日付**: {today.strftime('%Y年%m月%d日')}  ",
        f"**ユーザー**: [{USER}](https://atcoder.jp/users/{USER})  ",
        f"**コンテスト**: [{contest_id.upper()}](https://atcoder.jp/contests/{contest_id})\n",
        "> このレポートは GitHub Actions により自動生成されました。\n",
        "---\n",
    ]

    for item in problem_results:
        index = item["index"]
        title = item["title"]
        result = item["result"]
        sub = item["submission"]
        ai_text = item["ai_text"]

        badge = "✅ AC" if result == "AC" else f"❌ {result}"
        lines += [
            f"## 問題{index}: {title}\n",
            "| 項目 | 内容 |",
            "|------|------|",
            f"| 提出結果 | **{badge}** |",
            f"| 言語 | {sub.get('language', 'N/A')} |",
            f"| 実行時間 | {sub.get('execution_time', 'N/A')} ms |",
            f"| 提出リンク | [#{sub['id']}](https://atcoder.jp/contests/{contest_id}/submissions/{sub['id']}) |\n",
            ai_text,
            "\n---\n",
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main() -> None:
    now = datetime.now(JST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M JST')}] ABC Auto Reporter 起動")

    contest = get_todays_abc_contest()
    if not contest:
        print("本日開催のABCコンテストが見つかりませんでした。終了します。")
        sys.exit(0)

    contest_id = contest["id"]
    contest_num = re.sub(r"\D", "", contest_id)  # "abc456" → "456"
    date_str = now.strftime("%m%d")
    output_filename = f"{contest_num}_{date_str}.md"
    print(f"コンテスト: {contest_id.upper()}")

    submissions = get_user_submissions(USER, contest["start_epoch_second"])
    latest = latest_per_problem(submissions, contest_id)

    if not latest:
        print(f"{USER} の提出が見つかりませんでした。終了します。")
        sys.exit(0)

    print(f"対象問題数: {len(latest)}")

    problem_results = []
    for problem_id, sub in sorted(latest.items()):
        index = problem_id.split("_")[-1].upper()  # "abc456_c" → "C"
        result = sub["result"]
        print(f"  問題{index} ({result}) 処理中...")

        problem_info = scrape_problem(contest_id, problem_id)
        time.sleep(1.5)

        source_code = scrape_submission_code(contest_id, sub["id"])
        time.sleep(1.0)

        ai_text = generate_ai_explanation(
            problem_info["title"],
            problem_info["statement"],
            result,
            source_code,
        )
        time.sleep(1.0)

        problem_results.append(
            {
                "index": index,
                "title": problem_info["title"],
                "result": result,
                "submission": sub,
                "ai_text": ai_text,
            }
        )

    report = build_report(contest_id, contest_num, now, problem_results)

    output_path = Path(__file__).parent.parent / output_filename
    output_path.write_text(report, encoding="utf-8")
    print(f"レポートを保存しました: {output_filename}")


if __name__ == "__main__":
    main()
