import time
import requests
import toml
import jwt # PyJWT
import os

def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        return None, f"Exception parsing key: {e}"

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret.encode("utf-8"),
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    ), None

# 1. 키 읽기
try:
    with open(r'd:\AI프로그램제작\사전영업대시보드\.streamlit\secrets.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
        api_key = config['zhipuai']['api_key'].strip()
except Exception as e:
    print(f"Error reading secrets: {e}")
    exit()

print(f"Key format check: Length={len(api_key)}, Contains dot={'.' in api_key}")
print(f"System Time: {time.ctime()} ({time.time()})")

# 2. 강제로 과거 시간(2024년 1월)으로 토큰 생성 시도 (시스템 시간이 미래일 경우 대비)
# 만약 현재가 2025년이고 실제가 2024년이라면, 1년(31536000초)을 뺍니다.
fake_now = time.time() - 31536000 # 1년 전
payload_past = {
    "api_key": api_key.split(".")[0],
    "exp": int(round(fake_now * 1000)) + 600 * 1000, # 10분 유효
    "timestamp": int(round(fake_now * 1000)),
}

secret = api_key.split(".")[1]
token_past = jwt.encode(
    payload_past,
    secret.encode("utf-8"),
    algorithm="HS256",
    headers={"alg": "HS256", "sign_type": "SIGN"},
)

print("\nTrying with System Time Token (Standard SDK behavior)...")
# SDK 사용과 유사하게 호출 (생략 - 이미 실패함)

print("\nTrying with '1 Year Ago' Timestamp Token (Manual Request)...")
headers = {
    "Authorization": f"Bearer {token_past}",
    "Content-Type": "application/json"
}
data = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "Hello"}]
}

try:
    resp = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=data)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Request failed: {e}")
