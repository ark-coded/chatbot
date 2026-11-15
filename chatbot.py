#AI will be my portfolio and tell about my, hobby, projects, skills etc.   
#detailed system prompt. tell to ai as much as possible. tell AI to be honest.
#use fastapi. make a frontend which connects to fastapi background
#connect frontend and backend.
#HR can uload file or paste job description
#deploy backend on render / railway
#push on github 
#keep enhancing the project
import os
import time
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq
from pydantic import BaseModel


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key = api_key)

#I will create JSON about me now
