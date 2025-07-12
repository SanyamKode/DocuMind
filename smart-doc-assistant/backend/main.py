from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
import pandas as pd
import openpyxl
import io
import os
from typing import List, Dict, Optional
import tempfile
import json
import uuid
from groq import Groq
from datetime import datetime

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

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        self.created_at = datetime.now()

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            text += f"\n--- Page {i+1} ---\n"
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_data_from_excel(file_content: bytes) -> str:
    """Extract data from Excel file with improved formatting"""
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        result = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            result.append(f"\n=== Sheet: {sheet_name} ===")
            result.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            result.append(f"Columns: {', '.join(df.columns.tolist())}\n")
            
            # Convert data to string with better formatting
            if len(df) > 0:
                # Show first 100 rows for context
                display_df = df.head(100)
                result.append(display_df.to_string(index=False))
                if len(df) > 100:
                    result.append(f"\n... and {len(df) - 100} more rows")
            
            result.append("\n")
        
        return "\n".join(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading Excel: {str(e)}")

def truncate_content(content: str, max_chars: int = 30000) -> str:
    """Truncate content to fit within token limits"""
    if len(content) > max_chars:
        return content[:max_chars] + "\n\n[Content truncated due to length...]"
    return content

def call_groq_api(prompt: str, model: str = "llama-3.2-90b-text-preview") -> str:
    """Call Groq API with error handling"""
    try:
        # Available models: llama-3.2-90b-text-preview, llama-3.1-70b-versatile, mixtral-8x7b-32768
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a smart document assistant specialized in analyzing financial documents, spreadsheets, and business data. Provide clear, accurate, and helpful responses based on the document content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=model,
            temperature=0.1,  # Lower temperature for more consistent responses
            max_tokens=2000,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        # Fallback to smaller model if needed
        if "llama-3.2-90b" in model:
            return call_groq_api(prompt, "llama-3.1-70b-versatile")
        raise HTTPException(status_code=500, detail=f"AI API Error: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Smart Document Assistant API is running!",
        "model": "Powered by Groq with Llama 3.2",
        "endpoints": {
            "upload": "/upload",
            "ask": "/ask",
            "health": "/health"
        }
    }

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
        
        # Truncate content for API limits
        truncated_content = truncate_content(extracted_text)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store session
        document_sessions[session_id] = DocumentSession(
            filename=file.filename,
            content=truncated_content,
            doc_type=doc_type
        )
        
        # Clean up old sessions (keep only last 100)
        if len(document_sessions) > 100:
            oldest_sessions = sorted(document_sessions.items(), 
                                   key=lambda x: x[1].created_at)[:len(document_sessions)-100]
            for session_id, _ in oldest_sessions:
                del document_sessions[session_id]
        
        # Get initial summary
        prompt = f"""Analyze this {doc_type} document and provide a comprehensive summary.

Document: {file.filename}

Content:
{truncated_content[:8000]}

Please provide:
1. Document type and purpose
2. Key information and main topics
3. For financial documents: highlight important numbers, dates, and trends
4. For data files: describe the structure and type of data
5. Any notable findings or areas of interest

Keep the summary concise but informative."""
        
        try:
            summary = call_groq_api(prompt)
        except:
            summary = f"Document uploaded successfully. This is a {doc_type} file named '{file.filename}' with {len(extracted_text)} characters of content. Ask questions to analyze specific aspects of the document."
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "initial_summary": summary,
            "content_length": len(extracted_text),
            "truncated": len(extracted_text) > 30000
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
        
        # Build context with relevant parts of the document
        # For better performance, we'll try to find relevant sections
        question_lower = question.question.lower()
        
        # Extract relevant sections if the document is large
        relevant_content = session.content
        if len(session.content) > 10000:
            lines = session.content.split('\n')
            relevant_lines = []
            
            # Find lines that might be relevant to the question
            keywords = question_lower.split()
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords if len(keyword) > 3):
                    # Include context lines
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    relevant_lines.extend(lines[start:end])
            
            if relevant_lines:
                relevant_content = '\n'.join(relevant_lines[:200])  # Limit lines
            else:
                # If no specific matches, use beginning and end
                relevant_content = '\n'.join(lines[:100] + ['...'] + lines[-50:])
        
        # Build prompt
        prompt = f"""You are analyzing a {session.doc_type} document: {session.filename}

Previous questions in this session:
{json.dumps(session.chat_history[-3:], indent=2) if session.chat_history else "None"}

Document content (relevant sections):
{relevant_content}

User question: {question.question}

Instructions:
1. Answer based ONLY on the document content provided
2. If the document contains financial data, include specific numbers and calculations
3. For data questions, provide exact values from the document
4. If information is not found in the document, clearly state that
5. Format numbers properly (e.g., $1,234,567 for currency)
6. Be concise but thorough

Answer:"""
        
        # Get response from Groq
        response = call_groq_api(prompt)
        
        # Update chat history
        session.chat_history.append({
            "question": question.question,
            "answer": response
        })
        
        return {
            "answer": response,
            "session_id": question.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
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
        "history": session.chat_history,
        "created_at": session.created_at.isoformat()
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
    """Health check endpoint"""
    try:
        # Test Groq API
        test_response = call_groq_api("Say 'OK' if you're working", "llama-3.1-8b-instant")
        api_status = "healthy" if "OK" in test_response else "degraded"
    except:
        api_status = "unhealthy"
    
    return {
        "status": "healthy",
        "api_status": api_status,
        "sessions": len(document_sessions),
        "model": "Groq/Llama 3.2"
    }

@app.get("/models")
async def list_models():
    """List available AI models"""
    return {
        "models": [
            {
                "id": "llama-3.2-90b-text-preview",
                "name": "Llama 3.2 90B (Best)",
                "description": "Most capable model for complex analysis"
            },
            {
                "id": "llama-3.1-70b-versatile",
                "name": "Llama 3.1 70B",
                "description": "Balanced performance and speed"
            },
            {
                "id": "mixtral-8x7b-32768",
                "name": "Mixtral 8x7B",
                "description": "Fast responses, good for simple queries"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
