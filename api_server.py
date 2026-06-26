import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
from textblob import TextBlob

# Import existing ML models & Database from your streamlit_project
from database import init_db, save_document, get_document_by_id
from predict import run_prediction
from clause_classifier import classify_clauses
from risk_analyzer import analyze_risk
from paraphrase import paraphrase

app = FastAPI(
    title="Legal AI Analysis API",
    description="A decoupled REST API providing machine learning capabilities for Legal Document Analysis.",
    version="1.0.0"
)

# Allow CORS for external frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the SQLite database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# ---- Request Models ----
class ChatRequest(BaseModel):
    question: str

class ParaphraseRequest(BaseModel):
    text: str

# ---- API Endpoints ----

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Legal AI API is running."}

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF or TXT file, extracts text, saves it to the local SQLite DB, 
    and returns a unique document_id.
    """
    if file.filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file.file)
        document_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                document_text += text + "\\n"
    elif file.filename.endswith('.txt'):
        content = await file.read()
        document_text = content.decode("utf-8")
    else:
         raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
         
    doc_id = save_document(file.filename, document_text, None, None, None)
    return {"message": "Upload successful", "document_id": doc_id, "filename": file.filename}

@app.get("/api/v1/documents/{document_id}/analyze")
def analyze_document(document_id: int):
    """
    Fetches the document text from the database by ID and runs both
    Clause Classification and Risk Analysis pipelines.
    """
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    document_text = doc['content']
    
    # 1. Clause Classification
    clauses = classify_clauses(document_text)
    
    # 2. Risk Analysis
    risk = analyze_risk(document_text, clauses, [])
    
    return {
        "document_id": document_id,
        "filename": doc['filename'],
        "analysis_results": {
            "clauses": clauses,
            "risk_assessment": risk
        }
    }

@app.post("/api/v1/documents/{document_id}/chat")
def chat_with_document(document_id: int, request: ChatRequest):
    """
    Asks the RoBERTa ML model a question based on the document text.
    """
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    try:
        predictions_list = run_prediction(
            [request.question],
            doc['content'],
            'marshmellow77/roberta-base-cuad',
            n_best_size=3
        )
        
        answer_data = []
        if predictions_list and len(predictions_list) > 0:
             top_answers = predictions_list[0]
             for pred in top_answers:
                 clean_answer = pred['answer'].strip()
                 if len(clean_answer) < 2 or pred['score'] < 0.005: continue
                 
                 sentiment = "Neutral"
                 blob = TextBlob(clean_answer)
                 if blob.sentiment.polarity > 0.1: sentiment = "Positive"
                 elif blob.sentiment.polarity < -0.1: sentiment = "Negative"
                 
                 answer_data.append({
                     "text": clean_answer,
                     "confidence": round(pred['score'] * 100, 1),
                     "sentiment": sentiment
                 })
                 
        return {"question": request.question, "answers": answer_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model Error: {str(e)}")

@app.post("/api/v1/paraphrase")
def apply_paraphrase(request: ParaphraseRequest):
    """
    Simplifies complex legal jargon using the T5 model.
    """
    try:
        explanation = paraphrase(request.text)
        return {"original": request.text, "paraphrased": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
