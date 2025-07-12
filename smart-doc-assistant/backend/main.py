from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
import pandas as pd
import openpyxl
import io
import os
from typing import List, Dict
import tempfile
import json
import uuid
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load local or hosted model (e.g., llama2, mistral)
tokenizer = AutoTokenizer.from_pretrained("TheBloke/Mistral-7B-Instruct-v0.1-GGUF")
model = AutoModelForCausalLM.from_pretrained("TheBloke/Mistral-7B-Instruct-v0.1-GGUF")
generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

# Store document sessions (in production, use Redis or database)
document_sessions = {}

class Question(BaseModel):
    session_id: str
    question: str

class DocumentSession:
    def __init__(self, filename: str, content: str, doc_type: str):
        self.filename = filename
        self.content = content
        self.doc_type = doc_type
        self.chat_history = []

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_data_from_excel(file_content: bytes) -> str:
    """Extract data from Excel file"""
    try:
        df_dict = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
        result = []
        for sheet_name, sheet_df in df_dict.items():
            result.append(f"=== Sheet: {sheet_name} ===")
            result.append(sheet_df.to_string())
            result.append("\n")
        return "\n".join(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading Excel: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Smart Document Assistant API is running!"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        # Validate file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Extract text based on file type
       if file.filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(content)
            doc_type = "PDF"
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            extracted_text = extract_data_from_excel(content)
            doc_type = "Excel"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF or Excel files.")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store session
       document_sessions[session_id] = DocumentSession(
            filename=file.filename,
            content=extracted_text[:50000],
            doc_type=doc_type
        )

        prompt = f"""You are a smart document assistant. I've uploaded a {doc_type} document.\n
        Please provide a brief overview of what this document contains.\n
        Document content:\n{extracted_text[:3000]}"""

        response = generator(prompt, max_new_tokens=300, do_sample=True, temperature=0.7)
        answer = response[0]['generated_text'].split(prompt)[-1].strip()

        return {
            "session_id": session_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "initial_summary": answer,
            "content_length": len(extracted_text)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(question: Question):
    try:
        session = document_sessions.get(question.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")

        context = f"""You are a smart assistant analyzing a {session.doc_type} document titled '{session.filename}'.\n
        Here is the document content:\n{session.content}\n
        User's question: {question.question}\n
        Answer concisely and use specific values if present.\n        """

        response = generator(context, max_new_tokens=300, do_sample=True, temperature=0.7)
        answer = response[0]['generated_text'].split(context)[-1].strip()

        session.chat_history.append({
            "question": question.question,
            "answer": answer
        })

        return {
            "answer": answer,
            "session_id": question.session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    session = document_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "filename": session.filename,
        "doc_type": session.doc_type,
        "history": session.chat_history
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a document session"""
    if session_id in document_sessions:
        del document_sessions[session_id]
        return {"message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "sessions": len(document_sessions)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
