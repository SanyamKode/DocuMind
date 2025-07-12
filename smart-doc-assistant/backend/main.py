from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import PyPDF2
import pandas as pd
import openpyxl
import io
import os
from typing import List, Dict
import tempfile
import json
import uuid

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

# Configure Gemini (you'll need to set GEMINI_API_KEY environment variable)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#model = genai.GenerativeModel('gemini-1.5-flash')
chat = genai.Chat()

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
            content=extracted_text[:50000],  # Limit content size
            doc_type=doc_type
        )
        
        # Get initial summary
        prompt = f"""You are a smart document assistant. I've uploaded a {doc_type} document.
        Please provide a brief overview of what this document contains.
        Focus on key information, numbers, and important details.
        
        Document content (first part):
        {extracted_text[:3000]}...
        """
        
        response = model.generate_content(prompt)
        
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "initial_summary": response.text,
            "content_length": len(extracted_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(question: Question):
    """Ask a question about the uploaded document"""
    try:
        # Get session
        session = document_sessions.get(question.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
        
        # Build context with chat history
        context = f"""You are a smart document assistant specialized in analyzing {session.doc_type} documents.
        You're helping with financial analysis, business insights, and data queries.
        
        Document: {session.filename}
        
        Document content:
        {session.content}
        
        User question: {question.question}
        
        Please provide a clear, detailed answer based on the document content. 
        If the document contains financial data, include specific numbers and calculations.
        If asked about suppliers, payments, or financial highlights, extract the relevant information.
        Format numbers nicely (e.g., $1,234,567).
        If information is not in the document, say so clearly.
        """
        
        # Generate response
        response = model.generate_content(context)
        
        # Update chat history
        session.chat_history.append({
            "question": question.question,
            "answer": response.text
        })
        
        return {
            "answer": response.text,
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
