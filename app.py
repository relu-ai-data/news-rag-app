import os
import sqlite3
import feedparser
from google import genai
from dotenv import load_dotenv
import numpy as np
import json
import time
import math

# --- 1. 環境構築 & API初期化 ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

DB_NAME = "news.db"

# --- 2. データベース初期化 ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (title TEXT PRIMARY KEY, summary TEXT, url TEXT, published TEXT, embedding TEXT)''')
    conn.commit()
    conn.close()

# --- 3. ベクトル変換（真実のモデル） ---
def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-2-preview",  # 苦労して見つけた名前
        contents=text
    )
    return result.embeddings[0].values

# --- 4. 類似度計算 ---
def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# --- 5. ニュース取得とベクトル保存 ---
def save_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/it.xml")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print("--- 最新ニュースの取得と蓄積を開始 ---")
    
    saved_count = 0
    # 最新5件だけ処理
    for entry in feed.entries[:5]:
        # すでに保存済みかチェック
        c.execute("SELECT title FROM news WHERE title=?", (entry.title,))
        if c.fetchone():
            continue
            
        try:
            # 💥 【修正ポイント】要約APIは使わず、元のテキストをそのまま使う！
            safe_summary = entry.get('summary', entry.title)
            
            # ベクトルの生成（これだけは検索に必要なので残す！）
            embedding_vector = get_embedding(entry.title)
            embedding_json = json.dumps(embedding_vector)
            
            # DBに保存
            c.execute("INSERT INTO news (title, summary, url, published, embedding) VALUES (?, ?, ?, ?, ?)",
                      (entry.title, safe_summary, entry.link, entry.published, embedding_json))
            print(f"✅ 保存完了: {entry.title}")
            saved_count += 1
            
            # 要約を削ったので2秒待機でOK
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ 保存スキップ（エラー）: {e}")
            time.sleep(2)
            
    conn.commit()
    conn.close()
    
    if saved_count == 0:
         print("新しいニュースはありませんでした。")

# --- 6. 意味検索（RAG）の実行 ---
def search_rag(query):
    # 1. ユーザーの質問をベクトル化
    query_embedding = get_embedding(query)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title, summary, url, embedding FROM news")
    rows = c.fetchall()
    
    results = []
    for row in rows:
        title, summary, url, embedding_json = row
        embedding = json.loads(embedding_json)
        
        # コサイン類似度計算
        dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
        norm_q = math.sqrt(sum(a * a for a in query_embedding))
        norm_e = math.sqrt(sum(b * b for b in embedding))
        score = dot_product / (norm_q * norm_e)
        
        results.append((score, title, summary, url))
    
    # 2. 上位2件に絞って軽量化
    top_results = sorted(results, key=lambda x: x[0], reverse=True)[:2]
    
    print("\n🔍 「" + query + "」に関連する知識を抽出しました")
    context_text = ""
    for score, title, summary, url in top_results:
        print(f"- [類似度 {score:.3f}]: {title}")
        context_text += f"タイトル: {title}\n内容: {summary}\n\n"

    # 3. プロンプトを短くしてAPIに送る
    final_prompt = f"以下のニュースを基に、質問「{query}」に100文字以内で回答して。\n\n{context_text}"

    print("\n🤖 AI分析中...")
    try:
        # モデル名は確実に2.0-flash。これで429が出るなら通信環境かAPIキー自体の問題
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=final_prompt
        )
        print("\n=== AI分析レポート ===")
        print(response.text)
    except Exception as e:
        print(f"\n❌ AI分析失敗: {e}")
        print("※1分間待機するか、テザリング等でIPを変えて試してみてくれ！")

    conn.close()

# --- 6. メイン処理 ---
if __name__ == "__main__":
    user_query = input("\n検索キーワードを入力（Enterで最新取得）: ")
    if not user_query:
        save_news()
    else:
        search_rag(user_query)