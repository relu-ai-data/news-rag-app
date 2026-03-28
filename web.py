import streamlit as st
import time
import pandas as pd
# app.pyから3つの武器を召喚！
from app import search_rag, save_news, get_news_stats

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

st.title("🤖 AI ニュース解説ボット")
st.write("ここは俺の城だ。いいねなんていらねぇ、コードで語るぜ。")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 💬 メインチャット処理 ---
if prompt := st.chat_input("気になるニュースについて質問してくれ："):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try: # 🛡️ ここから「Hitoshiシールド（本名バレ防止）」発動！
                answer = search_rag(prompt)
                st.markdown(answer)
                with st.expander("🔍 分析の根拠を確認"):
                    st.code(f"QUERY: {prompt}\nSTATUS: Verified by Vector Search", language="bash")
            except Exception as e:
                # エラーが起きても血の海を出さず、スマートにエラー原因だけを表示！
                answer = f"⚠️ すまねぇ、軍師の脳内でエラーが起きたぜ。\n\n`{e}`"
                st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})