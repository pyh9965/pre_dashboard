from zhipuai import ZhipuAI
import toml

# Secrets 파일에서 키 읽기
try:
    with open(r'd:\AI프로그램제작\사전영업대시보드\.streamlit\secrets.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
        api_key = config['zhipuai']['api_key'].strip() # 공백 제거
except Exception as e:
    print(f"Error reading secrets: {e}")
    exit()

client = ZhipuAI(api_key=api_key)

models_to_test = [
    "GLM-4-Flash-250414",  # 최신 공식
    "GLM-4-Air-250414",    # 최신 공식
    "glm-4-flash",
    "glm-4",
    "chatglm_turbo"
]

print(f"Testing API Key: {api_key[:5]}...{api_key[-5:]}")

for model_name in models_to_test:
    print(f"\nTesting model: {model_name}...")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(f"SUCCESS! Model '{model_name}' works.")
        print(f"Response: {response.choices[0].message.content}")
        break # 하나 성공하면 종료
    except Exception as e:
        print(f"FAILED: {e}")
