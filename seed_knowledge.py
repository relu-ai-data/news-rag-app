import sqlite3
import json
from app import get_embedding # 既存のGemini埋め込み機能を使うぜ！

# 注入する知識リスト（ここを増やせば増やすほど賢くなる）
BASIC_KNOWLEDGE = [
    {"category": "Company", "content": "Sakana AIは、東京を拠点とするAIスタートアップ企業です。元Googleの研究者が設立し、生物の進化のような手法で効率的なAIを作る『進化モデルマージ』などで世界的に注目されています。"},
    {"category": "Term", "content": "RAG（検索拡張生成）とは、AIが自分の知らない情報を外部のデータベースから検索して、その内容に基づいて回答する仕組みのことです。このアプリもRAGで動いています。"},
    {"category": "Term", "content": "LLM（大規模言語モデル）とは、人間のように自然な文章を読み書きできるAIの知能のことです。GeminiやChatGPTなどがその代表例です。"}
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