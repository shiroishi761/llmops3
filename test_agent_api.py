import httpx
import json

# テスト用データ
test_data = {
    "input_data": {
        "ocr_content": """# 御見積書

**PAGE** 1/1  
**No.**00001462  
**見積日** 2024年10月06日

##宛先
萩森様

## 発行者情報
**会社名:** 株式会社グラフト 
**住所:** 〒619-0241 京都府相楽郡精華町祝園狛ヶ坪5番地  

##   御見積合計金額
**¥1,463,369-**

## 明細

| 商品名 |   単位 | 数量 | 単価 | 金額 | 備考   |
|--------|------|------|------|------|------|
| 仮設浄水  | ㎡ | 357.6 | 150 | 53,640 |  *数量のほうんでいません、現地も一個に役済資します。 |
"""
    },
    "config": {
        "prompts": [
            {
                "llm_name": "extraction_service",
                "prompt_name": "invoice_extraction_prompt_v1"
            },
            {
                "llm_name": "validation_service",
                "prompt_name": "react_evaluation_prompt"
            }
        ]
    }
}

# APIを呼び出し
url = "http://localhost:8000/llm/agent/invoice-with-validation"
response = httpx.post(url, json=test_data, timeout=60.0)

print(f"Status Code: {response.status_code}")
print(f"Response Keys: {list(response.json().keys())}")
print(f"Success: {response.json()['success']}")
print(f"Data Keys: {list(response.json()['data'].keys()) if response.json().get('data') else 'No data'}")

# dataの中身を確認
if response.json().get('data'):
    data = response.json()['data']
    print(f"\nData content (first 500 chars): {str(data)[:500]}")
else:
    print("\nNo data in response")

# 全体のレスポンスを保存
with open("agent_response.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=2)
print("\nFull response saved to agent_response.json")