import os
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Chat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Missing OPENAI_API_KEY")

SESSION_MEMORY: Dict[str, List[dict]] = {}

def trim_history(messages: List[dict], keep_last: int = 12) -> List[dict]:
    return messages[-keep_last:]

class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str

class HistoryRequest(BaseModel):
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "index.html not found", 404

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/history")
async def get_history(req: HistoryRequest):
    history = SESSION_MEMORY.get(req.session_id, [])
    return {"history": history}

@app.post("/ask")
async def ask_endpoint(req: ChatRequest):
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(400, "Message cannot be empty.")

    history = SESSION_MEMORY.setdefault(req.session_id, [])
    history.append({"role": "user", "content": user_msg})

    async def generate():
        full_reply = []
        usage_data = None
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful and concise study assistant."
                    },
                    *history
                ],
                temperature=0.7,
                max_tokens=400,
                stream=True,
                stream_options={"include_usage": True}
            )

            for chunk in stream:
                if chunk.usage:
                    usage_data = chunk.usage
                
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_reply.append(delta)
                    payload = {"content": delta}
                    yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            error_msg = f"\n[שגיאה בתקשורת: {str(e)}]"
            full_reply.append(error_msg)
            payload = {"content": error_msg}
            yield f"data: {json.dumps(payload)}\n\n"

        assistant_text = "".join(full_reply).strip()
        if assistant_text:
            history.append({"role": "assistant", "content": assistant_text})
            SESSION_MEMORY[req.session_id] = trim_history(history)

        # שליחת נתוני הטוקנים בסיום התשובה אם קיימים
        if usage_data:
            usage_payload = {
                "usage": {
                    "prompt_tokens": usage_data.prompt_tokens,
                    "completion_tokens": usage_data.completion_tokens,
                    "total_tokens": usage_data.total_tokens
                }
            }
            yield f"data: {json.dumps(usage_payload)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")