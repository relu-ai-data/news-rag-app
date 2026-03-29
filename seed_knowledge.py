import sqlite3
import json
from app import get_embedding # 既存のGemini埋め込み機能を使うぜ！

# 注入する知識リスト（ここを増やせば増やすほど賢くなる）
BASIC_KNOWLEDGE = [
    {"category": "Company", "content": "Sakana AIは、東京を拠点とするAIスタートアップ企業です。元Googleの研究者が設立し、生物の進化のような手法で効率的なAIを作る『進化モデルマージ』などで世界的に注目されています。"},
    {"category": "Term", "content": "RAG（検索拡張生成）とは、AIが自分の知らない情報を外部のデータベースから検索して、その内容に基づいて回答する仕組みのことです。このアプリもRAGで動いています。"},
    {"category": "Term", "content": "LLM（大規模言語モデル）とは、人間のように自然な文章を読み書きできるAIの知能のことです。GeminiやChatGPTなどがその代表例です。"},
    # --- ここから面接対策用の増強知識 ---
    {"category": "Term", "content": "ハルシネーション（Hallucination）とは、AIがもっともらしい嘘や事実に基づかない情報を生成してしまう現象のことです。RAGはこのハルシネーションを防ぐための有効な対策の一つです。"},
    {"category": "Company", "content": "OpenAIは、ChatGPTや動画生成AIなどを開発するアメリカのAI企業です。生成AIブームの火付け役となりました。"},
    {"category": "Company", "content": "Anthropic（アンスロピック）は、元OpenAIのメンバーが設立したAI企業です。安全性に特化したLLM「Claude（クロード）」シリーズを開発しています。"},
    {"category": "Company", "content": "NVIDIA（エヌビディア）は、AIの学習や推論に不可欠なGPU（画像処理半導体）で世界トップシェアを誇るメーカーです。"},
    {"category": "Term", "content": "ファインチューニング（微調整）とは、既存のAIモデルに特定の専門知識や自社のデータを追加学習させ、特定のタスクに特化させる技術のことです。"},
    {"category": "Term", "content": "プロンプトエンジニアリングとは、AIから目的の回答を正確に引き出すために、入力する指示文（プロンプト）を工夫・最適化するスキルのことです。"},
    {"category": "Term", "content": "ベクトルデータベースとは、テキストや画像を数値の配列（ベクトル）に変換して保存し、意味が似ているデータを高速に検索できるデータベースのことです。AIの記憶装置として使われます。"}
]

def seed():
    conn = sqlite3.connect("news.db")
    
    print("🧠 知識の種をまいています...")
    for item in BASIC_KNOWLEDGE:
        # すでに同じ内容がないかチェック
        exists = conn.execute("SELECT 1 FROM knowledge WHERE content = ?", (item['content'],)).fetchone()
        if not exists:
            embedding = get_embedding(item['content'])
            conn.execute(
                "INSERT INTO knowledge (category, content, embedding) VALUES (?, ?, ?)",
                (item['category'], item['content'], json.dumps(embedding))
            )
            print(f"✅ 追加完了: {item['content'][:20]}...")
    
    conn.commit()
    conn.close()
    print("✨ すべての知識が定着しました！")

if __name__ == "__main__":
    seed()