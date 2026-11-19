#use fastapi. make a frontend which connects to fastapi background
#connect frontend and backend.
#HR can upload file
#deploy backend on render / railway
#keep enhancing the project
import os
import time
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq
from pydantic import BaseModel


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
sys = f"""
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
sys_msg = {"role" : "system", "content" : sys}
messages = [sys_msg, user_msg]
#keeping sys_prompt + last 10 msges in the memory
def keep(messages) :
    if(len(messages) <= 11) :
        return messages
    return messages[0] + messages[-10:]
#Memory part
while(True) :
    completion = client.chat.completions.create(
        model=model,
        messages=keep(messages),
        stream = True
    )
    res = ""
    for chunk in completion:
        ans = chunk.choices[0].delta.content
        print(ans, end ="", flush = True)
        res += ans or ""
    time.sleep(2)
    messages.append({"role": "assistant", "content": res})
    usr = input()
    messages.append({"role" : "user", "content" : usr})

