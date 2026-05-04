# AtCoder-MySolutions

AtCoder ABC の解法記録リポジトリです。
2025年2月〜3月は問題文・コード・考察を**手動で記録**し、2025年5月からは **GitHub Actions + Google Gemini API** による**完全自動生成**に移行しました。

---

## 解法一覧

### 手動記録（〜2025年5月）

問題文・制約・入出力・自分のコード・考察を自分の言葉でまとめたノートです。

| ファイル | コンテスト | 日付 |
|---------|-----------|------|
| [0207.txt](0207.txt) | ABC（番号不明） | 2025/02/07 |
| [0214.txt](0214.txt) | ABC（番号不明） | 2025/02/14 |
| [0221.txt](0221.txt) | ABC（番号不明） | 2025/02/21 |
| [447_0228.txt](447_0228.txt) | ABC447 | 2025/02/28 |
| [449_0314.txt](449_0314.txt) | ABC449 | 2025/03/14 |
| [450_0321.txt](450_0321.txt) | ABC450 | 2025/03/21 |
| [451_0328.txt](451_0328.txt) | ABC451 | 2025/03/28 |
| [452_0404.txt](452_0404.txt) | ABC452 | 2025/04/04 |
| [453_0411.txt](453_0411.txt) | ABC453 | 2025/04/11 |
| [454_0418.txt](454_0418.txt) | ABC454 | 2025/04/18 |
| [455_0425.txt](455_0425.txt) | ABC455 | 2025/04/25 |
| [456_0502.txt](456_0502.txt) | ABC456 | 2025/05/02 |

### 自動生成レポート（2025年5月〜）

GitHub Actions が毎週土曜 23:00 JST に自動生成する AI 解説レポートです。

| ファイル | コンテスト | 内容 |
|---------|-----------|------|
| `(番号)_(MMDD).md` | 各週 ABC | AI 解説・模範解答・原因分析 |

---

## 自動化システムの仕組み

2025年5月より、手動記録を **GitHub Actions + Google Gemini API** で全自動化しました。

```
毎週土曜 23:00 JST
      │
      ▼
GitHub Actions 起動
      │
      ├─ AtCoder Problems API → uta516 の当日 ABC 提出を全取得
      │                         （問題ごとに最新の1提出を採用）
      ├─ AtCoder スクレイピング → 問題文・制約・入出力を取得
      ├─ 提出ページ スクレイピング → 提出コードを取得
      │
      ├─ Google Gemini API で解説を自動生成
      │     AC     → 最適解・アルゴリズム解説・計算量
      │     WA/TLE/RE → 不正解原因の分析 + 正解模範解答
      │
      └─ (コンテスト番号)_(MMDD).md を自動コミット・プッシュ
```

### 生成レポートの内容

| 提出結果 | 生成内容 |
|---------|---------|
| ✅ AC | アルゴリズム解説・計算量・Python 模範解答・実装のポイント |
| ❌ WA | 不正解原因（エッジケース漏れ等）の分析 + 正解模範解答 |
| ❌ TLE | 計算量の問題点の分析 + 最適化された正解模範解答 |
| ❌ RE/CE | エラー原因の特定 + 正解模範解答 |

---

## セットアップ手順（自動化システムの有効化）

### 1. GEMINI_API_KEY の取得

1. [Google AI Studio](https://aistudio.google.com/) にアクセスしてGoogleアカウントでサインイン
2. 左メニューの **Get API key** → **Create API key** をクリック
3. 生成されたキー（`AIza...` で始まる文字列）をコピーして安全な場所に保管

### 2. GitHub Secrets への登録

1. このリポジトリの **Settings** タブを開く
2. 左サイドバーの **Secrets and variables** → **Actions** を選択
3. **New repository secret** ボタンをクリック
4. 以下を入力して **Add secret** をクリック

   | フィールド | 値 |
   |-----------|-----|
   | Name | `GEMINI_API_KEY` |
   | Secret | `AIza...`（手順1でコピーしたキー） |

### 3. 動作確認（手動実行）

登録後すぐに動作確認する場合：

1. リポジトリの **Actions** タブを開く
2. 左サイドバーの **ABC Auto Report** を選択
3. **Run workflow** → **Run workflow** をクリック

> ABC コンテストが開催されていない日に手動実行した場合はスクリプトが正常終了し、レポートは生成されません。

---

## ファイル構成

```
AtCoder-MySolutions/
├── .github/
│   └── workflows/
│       └── abc_auto_report.yml   # GitHub Actions 定義（毎週土曜 23:00 JST）
├── scripts/
│   └── auto_reporter.py          # メインスクリプト
├── requirements.txt              # 依存パッケージ（google-generativeai / requests / bs4）
├── .gitignore
├── README.md
│
├── # ── 手動記録（〜2025年5月）─────────────────────
├── 0207.txt 〜 456_0502.txt      # 手書き解法ノート（12回分）
│
└── # ── 自動生成（2025年5月〜）─────────────────────
    └── (コンテスト番号)_(MMDD).md  # AI 解説レポート（例: 457_0510.md）
```

---

## 使用技術・API

| 技術 | 用途 |
|-----|------|
| [AtCoder Problems API](https://github.com/kenkoooo/AtCoderProblems) | 提出データ・コンテスト情報の取得 |
| [Google Gemini API](https://aistudio.google.com/) (`gemini-1.5-flash`) | AI 解説の生成（無料枠あり） |
| BeautifulSoup4 | 問題文・提出コードのスクレイピング |
| GitHub Actions | 毎週土曜 23:00 JST の自動実行 |
