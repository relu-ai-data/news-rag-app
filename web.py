import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import json
import google.generativeai as genai
from app import get_embedding
# app.pyから3つの武器を召喚！
from app import search_rag, save_news, get_news_stats

# --- プロっぽいUIにするためのCSS魔法 ---
st.markdown("""
    <style>
    /* 1. 全体のフォントをモダンに */
    html, body, [class*="css"]  {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 2. チャット入力欄（グレーの部分）を丸くし、主張の強い枠を消す */
    div[data-testid="stChatInputTextAreaContainer"] {
        border-radius: 25px !important; /* 角を丸く */
        padding: 5px 15px !important;
        border: 1px solid #ddd !important; /* 線の色を薄く */
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    /* 入力欄をクリックした時（フォーカス時）のスタイル（主張を抑え、赤を排除） */
    div[data-testid="stChatInputTextAreaContainer"]:focus-within {
        border-color: #555 !important; /* 主張のない薄いグレー */
        box-shadow: 0 0 0 0.1rem rgba(0,123,255,0.05) !important; /* 非常に薄い青 */
        outline: none !important;
    }

    /* 3. 送信アイコンを「紙ヒコーキ」風にする */
    /* デフォルトの↑マークを隠す */
    button[data-testid="stChatInputSubmitButton"] svg {
        display: none !important;
    }
    /* 代わりに紙ヒコーキ文字（Unicode）を入れる */
    button[data-testid="stChatInputSubmitButton"]::after {
        content: '➤'; /* 紙ヒコーキ風のアロー */
        font-size: 1.3rem;
        color: #555; /* アイコンの色 */
    }
    button[data-testid="stChatInputSubmitButton"]:hover::after {
        color: #007bff; /* ホバー時は青 */
    }
    
    /* 4. タイトル周りの余白を調整してスッキリさせる */
    .main .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🎨 ページ全体の設定 ---
st.set_page_config(
    page_title="World's No.1 DS Console",
    page_icon="🤖",
    layout="wide"
)

# # --- 🏰 サイドバー（管理パネル） ---
# with st.sidebar:
#     st.title("⚙️ 管理パネル")
#     st.write("世界一のデータサイエンティスト専用コンソール")
#     st.divider()
    
#     if st.button("🌐 最新ニュースを今すぐ取得"):
#         with st.spinner("世界中の情報を収集・解析中..."):
#             save_news()
#             st.success("データベースの更新が完了したぜ！")
#             time.sleep(1)
#             st.rerun()
            
#     st.divider()

#     # --- 📊 本物のデータ連携グラフ ---
#     st.subheader("📊 リアルタイム統計")
#     try:
#         # app.pyの関数を使って本物のデータをDBから取ってくる！
#         chart_data = get_news_stats()
#         if not chart_data.empty:
#             # グラフの描画（色分け対応版）
#             st.bar_chart(chart_data, x="source", y="count", color="source")
#         else:
#             st.write("まだ記事がないぜ。取得ボタンを押せ！")
            
#     except Exception as e:
#         st.write("データ取得中... またはエラーだぜ。")
#         st.write(e)

# # --- ここから下が「戦利品リスト」の独立したブロックだ！ ---
# st.sidebar.markdown("---") 
# st.sidebar.subheader("🛡️ 最新の戦利品（10件）")

# import sqlite3
# import pandas as pd

# try:
#     conn = sqlite3.connect("news.db")
#     # 魔法の言葉「ROWID DESC」で、最後に追加された10件を引っ張り出す！
#     df_latest = pd.read_sql_query("SELECT title, url FROM news ORDER BY ROWID DESC LIMIT 10", conn)
#     conn.close()

#     if not df_latest.empty:
#         for index, row in df_latest.iterrows():
#             # Markdownの力で「クリックできるリンク付きの箇条書き」を錬成！
#             st.sidebar.markdown(f"- [{row['title']}]({row['url']})")
#     else:
#         st.sidebar.write("まだ戦利品はないぜ。")
        
# except Exception as e:
#     st.sidebar.error(f"⚠️ 戦利品の取得に失敗したぜ: {e}")

#     st.divider()
#     st.write("▪️ ステータス: 稼働中")
#     st.write("▪️ エンジン: Gemini 2.5 Flash")
    
#     if st.button("会話履歴を消去"):
#         st.session_state.messages = []
#         st.rerun()
# --- 魔法のCSS（ここを追記！） ---
st.markdown("""
    <style>
        /* 右上のメニューボタン（三本線）やヘッダーを完全に隠す */
        header {visibility: hidden;}
        /* 一番下の「Made with Streamlit」を消す */
        footer {visibility: hidden;}
        /* スマホの画面の端っこまでチャット領域を広げる */
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- 🧠 チャット部分 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📰 AI News Insight Bot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 💬 メインチャット処理 ---
if prompt := st.chat_input("キーワードを入力してください（例: 最新のAI動向）"):
    
    # 1. ユーザーのメッセージを画面に表示 ＆ 記憶（session_state）に追加
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. アシスタント（AI）のメッセージを表示
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try: 
                # --- 直近の会話履歴をテキストにまとめる（最大4件分） ---
                history_text = ""
                # 現在の質問（1件）を除いた、過去のやり取りだけを抽出する
                if len(st.session_state.messages) > 1:
                    recent_msgs = st.session_state.messages[:-1][-4:]
                    for msg in recent_msgs:
                        role = "ユーザー" if msg["role"] == "user" else "アシスタント"
                        history_text += f"{role}: {msg['content']}\n"
                
                # 質問と一緒に、過去の履歴もsearch_ragに投げる！
                answer = search_rag(prompt, chat_history=history_text)
                # -----------------------------------------------------------------

                st.markdown(answer)
                
                with st.expander("🔍 分析の根拠を確認"):
                    st.code(f"QUERY: {prompt}\nSTATUS: Verified by Vector Search", language="bash")
                    
            except Exception as e:
                answer = f"⚠️ エラーが発生しました。\n\n`{e}`"
                st.error(answer)

        # アシスタントの回答を記憶に追加
        st.session_state.messages.append({"role": "assistant", "content": answer})