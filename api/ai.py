# api/ai.py (Updated to use the OpenAI library)

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai  # 1. Import the openai library

# Define the request body model (remains the same)
class Question(BaseModel):
    query: str

# Create a new router (remains the same)
router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"]
)

# Get the API Key from environment variables (do NOT hardcode secrets)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 2. Create an OpenAI client that is configured to connect to DeepSeek's API
# This is the core of the change. We are telling the official OpenAI library
# to send its requests to a different server (base_url).
if DEEPSEEK_API_KEY:
    client = openai.OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
else:
    client = None  # 保持 None，以便在缺少密钥时返回 500 错误并提示配置问题

# Create our core API endpoint
@router.post("/chat")
async def chat_with_deepseek(question: Question):
    """
    Receives a user's question and uses the OpenAI library to get a reply from the DeepSeek API.
    """
    if not client:
        raise HTTPException(status_code=500, detail="DeepSeek API Key 未配置")

    try:
        # 3. Use the familiar client.chat.completions.create method
        # The structure of this call is identical to how you would call OpenAI's GPT-4.
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",  # Specify the DeepSeek model
            messages=[
                {"role": "system", "content": "你是一个名为'京西网'的电商平台的智能导购助手。请友好、简洁地回答用户关于商品的咨询。"},
                {"role": "user", "content": question.query}
            ]
        )
        
        # 4. Extract the reply just like you would with an OpenAI response
        ai_reply = chat_completion.choices[0].message.content
        
        return {"reply": ai_reply.strip()}

    # The OpenAI library raises its own specific error types, which is great for error handling
    except openai.APIConnectionError as e:
        print(f"无法连接到 DeepSeek API: {e.__cause__}")
        raise HTTPException(status_code=503, detail="无法连接到AI服务，请检查网络连接。")
    except openai.APIStatusError as e:
        print(f"DeepSeek API 返回错误状态码: {e.status_code} - {e.response}")
        raise HTTPException(status_code=e.status_code, detail="AI服务返回错误。")
    except Exception as e:
        print(f"与AI服务交互时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="AI服务内部错误。")

