# AtCoder-MySolutions

AtCoder の提出データを自動収集し、**Anthropic Claude API** で AI 解説レポートを生成するリポジトリです。
毎週土曜 23:00 JST に GitHub Actions が無人で起動し、その日の ABC コンテスト分析を自動コミットします。

---

## 仕組み

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
      ├─ Anthropic Claude API で解説を自動生成
      │     AC  → 最適解・アルゴリズム解説
      │     WA/TLE/RE → 不正解原因の分析 + 正解模範解答
      │
      └─ (コンテスト番号)_(MMDD).md を自動コミット・プッシュ
```

---

## セットアップ手順

### 1. ANTHROPIC_API_KEY の取得

1. [Anthropic Console](https://console.anthropic.com/) にアクセスしてアカウントを作成
2. **API Keys** メニューから **Create Key** をクリック
3. 生成されたキー（`sk-ant-...` で始まる文字列）をコピーして安全な場所に保管

### 2. GitHub Secrets への登録

1. このリポジトリの **Settings** タブを開く
2. 左サイドバーの **Secrets and variables** → **Actions** を選択
3. **New repository secret** ボタンをクリック
4. 以下を入力して **Add secret** をクリック

   | フィールド | 値 |
   |-----------|-----|
   | Name | `ANTHROPIC_API_KEY` |
   | Secret | `sk-ant-...`（手順1でコピーしたキー） |

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
├── requirements.txt              # 依存パッケージ
├── .gitignore
├── README.md
└── (コンテスト番号)_(MMDD).md    # 自動生成レポート（例: 456_0504.md）
```

---

## 生成レポートの内容

| 提出結果 | 生成内容 |
|---------|---------|
| ✅ AC | アルゴリズム解説・計算量・Python 模範解答・実装のポイント |
| ❌ WA | 不正解原因（エッジケース漏れ等）の分析 + 正解模範解答 |
| ❌ TLE | 計算量の問題点の分析 + 最適化された正解模範解答 |
| ❌ RE/CE | エラー原因の特定 + 正解模範解答 |

---

## 使用技術・API

| 技術 | 用途 |
|-----|------|
| [AtCoder Problems API](https://github.com/kenkoooo/AtCoderProblems) | 提出データ・コンテスト情報の取得 |
| [Anthropic Claude API](https://www.anthropic.com/) (`claude-sonnet-4-6`) | AI 解説の生成 |
| BeautifulSoup4 | 問題文・提出コードのスクレイピング |
| GitHub Actions | 毎週土曜 23:00 JST の自動実行 |
