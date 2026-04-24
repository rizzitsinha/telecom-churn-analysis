"""
FastAPI backend — AI endpoints only.
No CSV loading. No pandas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Telecom Churn AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "You are a telecom churn analytics AI assistant for an Indian telecom consulting "
    "PoC dashboard covering 500,000 customers across 14 Indian cities. Answer "
    "analytically and concisely in 3–5 sentences unless asked for more detail. When "
    "discussing seasonal trends, reference Indian festivals (Diwali, IPL season, "
    "financial year end). When discussing bundles, use actual bundle names from the "
    "data. Never fabricate numbers — use only figures from the context object provided. "
    "If a question is outside the dashboard's scope, say so briefly."
)

model = genai.GenerativeModel("gemini-2.5-flash")


class ChatRequest(BaseModel):
    message: str
    context: dict


class HotspotRequest(BaseModel):
    hotspot_type: str
    hotspot_value: str
    stats: dict


@app.post("/api/ai/chat")
async def ai_chat(req: ChatRequest):
    user_message = (
        f"Dashboard context: {json.dumps(req.context)}\n\n"
        f"User question: {req.message}"
    )

    async def stream():
        try:
            response = model.generate_content(
                [
                    {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                    {"role": "model", "parts": [{"text": "Understood. I will act as the telecom churn analytics AI assistant."}]},
                    {"role": "user", "parts": [{"text": user_message}]},
                ],
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    data = chunk.text.replace("\n", "\\n")
                    yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/ai/hotspot")
async def ai_hotspot(req: HotspotRequest):
    prompt = (
        f"A telecom analyst clicked on [{req.hotspot_type}: {req.hotspot_value}] "
        f"on the churn dashboard. Here are the stats for this segment: "
        f"{json.dumps(req.stats)}. Give exactly 4 specific, actionable retention or "
        f"revenue recovery strategies for this segment in the context of Indian telecom "
        f"market conditions. Reference relevant competitors (Jio, Airtel, Vi) where "
        f"appropriate. Be direct. Start with '1.' No preamble. No closing summary."
    )

    async def stream():
        try:
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    data = chunk.text.replace("\n", "\\n")
                    yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
