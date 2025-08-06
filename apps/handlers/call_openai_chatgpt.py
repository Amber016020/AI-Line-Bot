from openai import OpenAI

client = OpenAI(api_key="sk-XXX")

def call_openai_chatgpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位理財助理，會根據使用者的支出紀錄提供簡單分析與生活化的建議。"
                                            "請根據使用者輸入的語言回覆，如果他使用中文，請回覆自然、口語化、清楚的繁體中文；"
                                            "如果使用英文，請回英文。"
                                            "請避免過於正式或書面化，讓回覆聽起來像一位親切又實用的生活助理。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "抱歉，目前無法處理你的問題，請稍後再試～"