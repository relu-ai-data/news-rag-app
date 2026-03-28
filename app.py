from datetime import datetime, timedelta
import os
import re
import sqlite3
DB_NAME = "news.db"
import sys
from datetime import datetime
from typing import Optional

import feedparser
from dotenv import load_dotenv
import os
from google import genai

# .envファイルからAPIキー（通行証）を読み込む！
load_dotenv()

def get_embedding(text):
    """テキストをAIの脳内座標（ベクトル）に変換する最強の関数だ！"""
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 🌟 モデルを最新の「gemini-embedding-001」にアップグレード！
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=text,
        # 🌟 昨日の6件（768次元）と形を合わせて計算のクラッシュを防ぐ魔法！
        config={'output_dimensionality': 768} 
    )
    return response.embeddings[0].values

FEED_URL = "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"
LIMIT = 5
MODEL_NAME = "gemini-2.5-flash"
DB_PATH = os.path.join(os.path.dirname(__file__), "news.db")


def summarize_title(client: genai.Client, title: str) -> str:
    """
    タイトルをGeminiに渡し、「データサイエンティストの卵であるエンジニアが読むべきポイント」を1行で返す。
    """

    prompt = (
        "あなたはデータサイエンティストの卵であるエンジニアです。"
        "次のニュースタイトルから、エンジニアが読むべきポイントを1行（改行なし）で日本語の1文に要約してください。"
        "回答は要約文のみ。ラベルや前置きは禁止です。\n"
        f"ニュースタイトル: {title}"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=types.Part.from_text(text=prompt),
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=600,
        ),
    )
    text = getattr(response, "text", "") or ""

    # 改行や連続する空白をまとめて、結果が「1行」になるよう整形する。
    return re.sub(r"\s+", " ", text).strip()


def get_existing_summary(conn: sqlite3.Connection, title: str) -> Optional[str]:
    cur = conn.execute("SELECT summary FROM news WHERE title = ?", (title,))
    row = cur.fetchone()
    return row[0] if row else None


def ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            title TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            url TEXT,
            embedding TEXT,
            fetched_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def save_news_if_new(
    conn: sqlite3.Connection,
    *,
    title: str,
    summary: str,
    url: str,
    fetched_at: str,
) -> bool:
    """
    news テーブルにタイトルが存在しない場合のみ保存する。
    既存の場合は保存しない（INSERT OR IGNORE）。
    """

    cur = conn.execute(
        "INSERT OR IGNORE INTO news (title, summary, url, fetched_at) VALUES (?, ?, ?, ?)",
        (title, summary, url, fetched_at),
    )
    conn.commit()
    # sqlite3 の rowcount は挙動が環境依存なことがあるが、PRIMARY KEY の INSERT OR IGNORE は
    # 通常 1/0 になるためその期待で判定する。
    return cur.rowcount == 1

def save_news():
    """複数のRSSからニュースを狩り集める真の広域スクレイピング版"""
    import feedparser
    import json
    
    # 🎯 特盛りリスト
    feed_urls = [
        "https://news.yahoo.co.jp/rss/topics/it.xml",
        "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
        "https://rss.itmedia.co.jp/rss/2.0/ai-ai.xml",
        "https://toyokeizai.net/list/feed/rss",
        "https://ascii.jp/ai/rss.xml",
        "https://jp.techcrunch.com/feed/",
    ]
    
    conn = sqlite3.connect(DB_NAME)
    
    # 1. まず絶対に「部屋（テーブル）」を作る！
    ensure_db(conn)
    
    # 2. 部屋ができたのを確認してから、掃除機を回す！
    cleanup_old_news(conn, days=7)
    
    cur = conn.cursor()
    saved_count = 0
    
    print("--- 🌐 広域ニュース収集を開始 ---")
    
    for feed_url in feed_urls:
        print(f"📡 取得中: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        # ⚡️ リミッター解除（全部狩る！）
        for entry in feed.entries:
            try:
                title = entry.title
                url = entry.link
                summary = entry.get('summary', title)
                
                # 🛡️ 真の重複チェック（URLがすでにDBにあるか確認）
                cur.execute("SELECT 1 FROM news WHERE url = ?", (url,))
                if cur.fetchone():
                    continue # すでにあるならスキップ！
                
                # ⚡️ ベクトルを生成（さっき直した最強の杖を発動）
                embedding_vector = get_embedding(summary)
                embedding_json = json.dumps(embedding_vector)
                
                # 💾 本物のカラム（embedding）に直接保存！
                cur.execute(
                    # 150行目付近をこう書き換える！
                    "INSERT INTO news (title, summary, url, embedding, fetched_at) VALUES (?, ?, ?, ?, ?)",
                    (title, summary, url, embedding_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                
                print(f"✅ 新規保存: {title}")
                saved_count += 1
                    
            except Exception as e:
                print(f"⚠️ 保存スキップ（エラー）: {e}")
                
    conn.commit()
    conn.close()
    print(f"--- 完了！新しく {saved_count} 件のニュースを保存したぜ ---")

def cleanup_old_news(conn, days=7):
    """古いニュースを消すための『掃除機』を定義する"""
    limit_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.execute("DELETE FROM news WHERE fetched_at < ?", (limit_date,))
    conn.commit()
    if cur.rowcount > 0:
        print(f"--- 🧹 古いニュースを {cur.rowcount} 件削除したぜ！ ---")

import numpy as np

import json # ベクトルを復元するのに使うぜ

def search_rag(query):
    # 1. 質問をベクトルに変換（★お前が元々持っている関数を使う！）
    query_embedding = get_embedding(query)
    
    # 2. DBから全記事を取得（★列名をお前のDBに正確に合わせたぜ！）
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT title, summary, embedding FROM news WHERE embedding IS NOT NULL", conn)
    conn.close()
    
    if df.empty:
        return "まだ記事がないぜ。まずはニュースを取得してくれ。"

    # 3. 類似度（スコア）を計算する
    # jsonで保存されたベクトルをリスト→numpy配列に変換
    df["embedding"] = df["embedding"].apply(json.loads).apply(np.array)
    q_vec = np.array(query_embedding)
    
    # ベクトルの内積（角度の近さ）を計算してスコア列を作る
    df["score"] = df["embedding"].apply(lambda x: np.dot(x, q_vec))
    
    # 4. スコアが高い（意味が近い）上位3件だけを抜粋！
    top_docs = df.sort_values("score", ascending=False).head(3)
    context_text = "\n\n".join([f"【{row['title']}】\n{row['summary']}" for _, row in top_docs.iterrows()])

    # 5. 選ばれし少量のデータだけを軍師Geminiに渡す（API節約＆高精度！）
    # 【修正】最新バージョンの genai に合わせた最強の呼び出し方だ！
    client = genai.Client()
    final_prompt = f"""
    お前は最強のAI軍師だ。以下の厳選されたニュースを基に、質問「{query}」に答えろ。
    文字数は200文字以内、相棒のような熱い口調でな。

    【厳選データ】
    {context_text}
    """
    
    # ここが最新版の回答生成コマンドだ
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=final_prompt
    )
    return response.text

import sqlite3
import pandas as pd

def get_news_stats():
    """URLから情報源を分析し、鮮やかな分割グラフの元データを作る関数だ！"""
    import pandas as pd
    import sqlite3
    
    try:
        conn = sqlite3.connect(DB_NAME)
        # データベースからURLだけを全部引っこ抜く！
        df = pd.read_sql_query("SELECT url FROM news", conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame({"source": ["データなし"], "count": [0]})
        
        # 🧙‍♂️ URLの文字列から情報源を判別する仕分けルール
        def get_source_name(url):
            if "yahoo" in url: return "Yahoo!"
            elif "itmedia" in url: return "ITmedia"
            elif "toyokeizai" in url: return "東洋経済"
            elif "ascii" in url: return "ASCII"
            elif "techcrunch" in url: return "TechCrunch"
            else: return "その他"
            
        # Pandasの強力なメソッド「apply」で全URLを一気に変換！
        df["source"] = df["url"].apply(get_source_name)
        
        # 情報源（source）ごとにグループ分けして数を数える
        stats_df = df.groupby("source").size().reset_index(name="count")
        
        return stats_df
        
    except Exception as e:
        print(f"⚠️ グラフデータ作成エラー: {e}")
        return pd.DataFrame({"source": ["エラー"], "count": [0]})

if __name__ == "__main__":
            save_news()