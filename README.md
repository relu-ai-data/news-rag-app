# 🤖 AI News 解説ボット (Hybrid-RAG Architecture)

シニア層でも迷わず使える「極限まで引き算されたUI」と、最新動向＆ドメイン知識を組み合わせた「ハイブリッドRAG」を搭載したニュース解説エージェントです。

## 🎯 プロジェクトの背景と課題解決

ITリテラシーが高くないユーザー（自身の家族）に最新のAIニュースに触れてもらうため、本アプリを開発しました。開発過程で得たフィードバックを基に、以下の課題解決を行っています。

1. **UX/UIの最適化（引き算のUI）**
   * **課題**: 当初は情報量の多いダッシュボード形式でしたが、ターゲット層には「どこを見ていいか分からない」と敬遠されました。
   * **解決策**: Streamlitの不要なヘッダーやフッターをCSS注入で強制非表示にし、「チャット入力欄のみ」の極限までシンプルなUIに改修。迷わず直感的に使えるデザインを実現しました。
2. **情報の網羅性とハルシネーション対策（ハイブリッドRAG）**
   * **課題**: 直近のニュースをベクトル検索する通常のRAG構成では、「Sakana AIとは？」などの基礎的な質問に対し、その週にニュースがないと「回答不能」になる弱点がありました。
   * **解決策**: SQLite内に「一定期間で削除される最新ニューステーブル」と「永続的な基礎知識テーブル（用語解説など）」の2層構造（ハイブリッド型）を構築。Pandasで動的に結合してからNumpyでベクトル検索（コサイン類似度計算）を行うことで、圧倒的な回答精度を実現しました。
3. **完全サーバーレスでのデータ更新（MLOps/CI・CD）**
   * **課題**: 毎日手動でニュースをスクレイピングし、DBを更新する運用コスト。
   * **解決策**: GitHub Actionsを用いて、毎日定時にニュース収集バッチ（Pythonスクリプト）を自動実行。取得・ベクトル化・古いデータのパージ・リポジトリへのPushまでを完全自動化しました。

## 🛠 技術スタック

* **言語**: Python 3.9+
* **LLM / Embedding**: Google Gemini API (`gemini-2.5-flash` / `text-embedding-004`)
* **Database**: SQLite3 (Pandas / Numpy による独自ベクトル検索実装)
* **Frontend**: Streamlit
* **CI/CD (Automation)**: GitHub Actions
* **Data Processing**: Feedparser, BeautifulSoup4

## ⚙️ システム構成 (Architecture)

1. **データ収集バッチ (GitHub Actions)**: 定期的にRSSフィードからニュースを取得し、Gemini APIでベクトル化して `news.db` を更新。
2. **静的ナレッジ**: `seed_knowledge.py` により、事前に定義されたAI用語などのドメイン知識をDBに永続化。
3. **推論エンジン**: ユーザーの質問をベクトル化し、ニュースと知識の両テーブルから類似度（内積）の高いコンテキストを抽出。Geminiにプロンプトとして渡し、正確で自然な回答を生成。

## 🚀 ローカル環境での動かし方

```bash
# リポジトリのクローン
git clone [https://github.com/君のユーザー名/news-rag-app.git](https://github.com/君のユーザー名/news-rag-app.git)
cd news-rag-app

# 依存パッケージのインストール
pip install -r requirements.txt

# APIキーの設定 (.envファイルを作成)
echo "GEMINI_API_KEY=あなたのAPIキー" > .env

# 基礎知識データの注入 (初回のみ)
python seed_knowledge.py

# ニュースデータの取得 (任意)
python check.py

# アプリの起動
streamlit run web.py