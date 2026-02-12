from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from model import ask_question
import database

app = FastAPI(title="Telegram QA Bot API")

# n8n Webhook URL
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/bot-events"

# Request schema
class AskRequest(BaseModel):
    conversation_id: str
    question: str

@app.get("/conversations")
def get_all_conversations():
    return database.list_conversations()

@app.post("/conversations")
def start_new_conversation():
    cid = database.create_conversation()
    return {"conversation_id": cid}

@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):
    return database.get_messages(conversation_id)

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    database.delete_conversation(conversation_id)
    return {"status": "success"}

# Endpoint for frontend to send question
@app.post("/ask")
def ask(req: AskRequest):
    if not req.conversation_id or not req.question:
        raise HTTPException(status_code=400, detail="conversation_id and question required")

    try:
        # Generate answer using LangChain
        answer = ask_question(req.question, req.conversation_id)

        # Send data to n8n webhook (optional logging)
        try:
            requests.post(N8N_WEBHOOK_URL, json={
                "conversation_id": req.conversation_id,
                "question": req.question,
                "answer": answer
            })
        except Exception as e:
            print("Failed to send to n8n:", e)

        return {"answer": answer}
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
