#use fastapi. make a frontend which connects to fastapi background
#connect frontend and backend.
#HR can upload file
#deploy backend on render / railway
#keep enhancing the project
import os
import time
import json
import io

from gradio_client import file
from chatbot.main import SYSTEM_PROMPT
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional
from groq import Groq
from pypdf import PdfReader
from pydantic import BaseModel

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")
client = Groq(api_key=api_key)
model = "openai/gpt-oss-120b"

experience = [{
    "Company" : "ADS Web Solutions, Kolkata",
    "Role" : "Junior SME Intern",
    "Duration" : "2 Months",
    "Description" : "Designed and structured Mathematics questions for mock tests, DPPs for students preparing for JEE.",
    "Skills_Used" : ["Problem Solving", "MS Word", "Team Work"]
    }, {
    "Company" : "InAmigos Foundation",
    "Role" : "AI / ML Intern",
    "Duration" : "2 Weeks",
    "Description" : "Hands on practice on training and understanding AI models.",
    "Skills_Used" : ["Artificial Intelligence", "Leadership"]
    }]

resume = {
    "Name" : "Arkaprabha Mallick",
    "Email" : "arkaprabhamallick@gmail.com",
    "Age" : 19,
    "Education" : ["Schools : Kendriya Vidyalaya No. 2 Ishapore, PM SHRI Kendriya Vidyalaya Burdwan", "College : B.Tech in Computer Science from Ideal Institute of Engineering 2nd Year"],
    "Total_Experience_Years" : 0.2,
    "Skills" : ["Artificial Intelligence", "Git", "Competitive Programming", "Object Oriented Programming", "Data Structures & Algorithms", "Cloud Computing", "Editing Softwares"],
    "Programming_Languages" : ["C++", "C", "Python", "Java", "JavaScript"],
    "Databases" : "MySQL",
    "Platforms" : ["LeetCode : https://leetcode.com/u/arkcodeshere", "CodeForces : https://codeforces.com/profile/arkcodes", "Github : https://github.com/ark-coded", "LinkedIn : https://www.linkedin.com/in/arkaprabha-mallick"],
    "Experience" : experience,
    "Projects" : ["AI ChatBot", "Resume Parser"],
    "Certifications" : None
    }

user_input = input()
user_msg = {"role" : "user", "content" : user_input}
SYSTEM_PROMPT = f"""
Here is my resume {resume}
#ROLE
You are a professional personal assistant of Arkaprabha Mallick.
#TASK
If: a job Description is given to you then list the things that matches from my resume with that job description.
else : Your job is to respond strictly from the resume. Do not invent anything on your own. Do not lie about any skill degree or something. If you are asked about meaning of anything that is inside the resume then you should answer to that correctly.
#CONSTRAINTS
Do not add anything from your own, the only data you have is the resume.
#OUTPUT FORMAT
Give output in easily readable by human format.
#EXAMPLES
"What is the first company he worked in" -> ans to this will be ADS Web Solutions
"Why no certificates" or similar -> its ans will be "Sorry I can't help you with that."
#FALLBACK
If the prompt is unrelated to my resume or any job description then return "Sorry, I only answer about technical / professional queries related to Arkaprabha Mallick."
"""

# In-memory session storage: session_id - list of messages
sessions: Dict[str, List[dict]] = {}
# Additional context per session 
session_context: Dict[str, str] = {}

app = FastAPI(title="ARK AI", description="A chatbot that answers questions about Arkaprabha Mallick", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


def get_session(session_id: str) -> List[dict]:
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return sessions[session_id]

def keep_messages(messages: List[dict]) -> List[dict]:
    """Keep system prompt + last 10 messages"""
    if len(messages) <= 11:
        return messages
    return [messages[0]] + messages[-10:]

async def stream_response(session_id: str, user_message: str):
    messages = get_session(session_id)

    # Add any extra context (e.g., from uploaded files)
    extra_context = session_context.get(session_id, "")
    if extra_context:
        user_message = f"[Additional context from uploaded file:\n{extra_context}\n]\n\nUser: {user_message}"

    messages.append({"role": "user", "content": user_message})
    messages = keep_messages(messages)

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )

    full_response = ""
    for chunk in completion:
        content = chunk.choices[0].delta.content
        if content:
            full_response += content
            yield f"data: {json.dumps({'content': content})}\n\n"

    messages.append({"role": "assistant", "content": full_response})
    sessions[session_id] = keep_messages(messages)
    yield f"data: {json.dumps({'done': True})}\n\n"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

@app.get("/")
async def root():
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("""
    <html><body style="font-family: system-ui; padding: 2rem; max-width: 600px; margin: 0 auto;">
        <h1>Resume Chatbot</h1>
        <p>Frontend not built yet. Run <code>python main.py</code> after creating frontend/index.html</p>
    </body></html>
    """)

@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        stream_response(request.session_id, request.message),
        media_type="text/event-stream"
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form("default")):
    content = await file.read()
    text = ""
    if file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.filename.endswith(".txt"):
        text = content.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files supported")
    #Context size shrinking
    if len(text) > 8000:
        text = text[:8000] + "\n[truncated]"

    session_context[session_id] = text
    return {"filename": file.filename, "chars": len(text), "session_id": session_id}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    session_context.pop(session_id, None)
    return {"cleared": True}