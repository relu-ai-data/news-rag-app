import os
import json
import urllib.request
from dotenv import load_dotenv

# 防弾チョッキから鍵を取り出す
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

print("🔍 Googleのサーバー（心臓部）を直接ハッキング中...")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    # SDKを使わず、素のHTTP通信で直接データを引っこ抜く
    with urllib.request.urlopen(url) as res:
        data = json.loads(res.read().decode())
        print("✅ サーバー侵入成功。ベクトル化モデルを抽出します...\n")
        
        for m in data.get("models", []):
            if "embedContent" in m.get("supportedGenerationMethods", []):
                # 使える名前だけを綺麗に表示
                name = m['name'].replace('models/', '')
                print(f"🎯 埋め込み可能モデル: {name}")
except Exception as e:
    print(f"❌ 通信エラー: {e}")