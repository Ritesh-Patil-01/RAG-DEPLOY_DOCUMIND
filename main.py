from fastapi import FastAPI 
from fastapi import HTTPException
from chunk import split_text  
from pydantic import BaseModel
from fastapi import UploadFile , File 
from pypdf import PdfReader
from groq import Groq
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil 
import os
import subprocess
import uuid
import re


app = FastAPI()               # creates fastAPI application 
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# welcome message :--->
@app.get("/")                 # decorator 
def home():
    return {"message":"Welcome"}


class TextRequest(BaseModel) :
    text : str                # this means " User MUST provide text "
    chunk_size :  int = 50 
    chunk_overlap :  int = 10 
class QueryRequest(BaseModel) :
    query :str        # this means " User MUST provide text in form of query"
class CodeRequest(BaseModel) :
    idea : str
class AnimationRequest(BaseModel) :
    idea : str


load_dotenv() 
client=Groq(api_key=os.getenv("GROQ_API_KEY"))

# Validation  and Error handling :--->
@app.post("/chunk")           
def chunk_text(data :TextRequest) :
    if not data.text.strip() :
        raise HTTPException(status_code=400,detail="text cannot be empty")
    
    if data.chunk_size <= 0 :
        raise HTTPException(status_code=400,detail="chunk_size to be > 0")
    
    if data.chunk_overlap < 0 :
        raise HTTPException(status_code=400,detail="chunk_overlap to be >=0")
    
    chunks = split_text(data.text,data.chunk_size,data.chunk_overlap)
    return {"chunks":chunks,"total_chunks":len(chunks)}

# 6.a :--->
@app.post("/csv")
async def read_csv(file : UploadFile=File(...)) :
    if not file.filename.endswith(".csv") :
        raise HTTPException(status_code=400,detail="not a valid csv format") 
    
    content = await file.read() 
    text = content.decode("utf-8")
    chunks = split_text(text)

    return{"filename":file.filename,"chunks":chunks,"total_chunks":len(chunks)}

# 6.b --->
@app.post("/pdf")
async def read_pdf(file : UploadFile=File(...)) :
    if not file.filename.endswith(".pdf") :
        raise HTTPException(status_code=400,detail="not a valid PDF format")
    
    reader = PdfReader(file.file)
    text=""

    for page in reader.pages :
        extracted = page.extract_text() 
        if extracted :
            text +=extracted +"\n" 

    chunks = split_text(text)

    return{"filename":file.filename,"chunks":chunks,"total_chunks":len(chunks)} 

# 6.c --->
@app.post("/ask") 
def question_LLM(data: QueryRequest) :
    if not data.query.strip() :
        raise HTTPException(status_code=400,detail="query cant be empty")
    
    response =client.chat.completions.create(
        model="llama-3.3-70b-versatile" ,
        messages=[{"role":"user","content":data.query}])
    answer = response.choices[0].message.content 

    return{"query":data.query,"answer":answer}

# 6.d --->
@app.post("/generate_code") 
def generate_code(data : CodeRequest) :
    if not data.idea.strip() :
        raise HTTPException(status_code=400,detail="cant be empty") 
    
    prompt =f"""generate only executable code 
                idea:{data.idea}
                return only the code . 
                do not add explanations and comments .
             """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}])
    code = response.choices[0].message.content

    return{"idea":data.idea,"generate_code":code}

# 6.e.1 ---> ( this is not the main e)
@app.post("/generate_manim")
def generate_manim(data: AnimationRequest) :
    if not data.idea.strip() :
        raise HTTPException(status_code=400,detail="cant be empty")
    
    prompt =f"""generate complete manim community edition code .
                animation idea :{data.idea} 
                return only python code .
                do not explain anything and do not add comments .    
             """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}])
    
    return{"idea":data.idea,"manim_code":response.choices[0].message.content}

# 6.e.main ---> ( this is the main e) 
@app.post("/generate_video")
def generate_video(data : AnimationRequest) :
    prompt =f"""generate one complete manim community edition script.
                requirements :-->
                exactly one scene class .
                name the scene , generatedscene .
                return only PYTHON code .
                no markdown or no comments .
                no explanations .
                animation idea :{data.idea} 
             """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}])
    code=response.choices[0].message.content
    code = re.sub(r"```python","",code)
    code = re.sub(r"```","",code)
    code = code.strip() 

    file_id = str(uuid.uuid4())[:8]
    python_file = f"generated_scripts/generated_{file_id}.py"
    with open(python_file,"w",encoding="utf-8") as x :
        x.write(code)

# rendering with manim :--->
    subprocess.run(["manim","-ql",python_file,"generatedscene"],check=True)  

# making it downloadable :---> 
    video_source = Path(f"media/videos/generated_{file_id}/480p15/GeneratedScene.mp4")
    video_destination = Path(f"videos/{file_id}.mp4")
    shutil.copy(video_source, video_destination)          

    return{"status":"sucess",
           "video_url":f"http://127.0.0.1:8000/videos/{file_id}.mp4"}