# Legal AI Assistant - Version 1

## Overview
This is the simplified version of the Legal AI Assistant with core Q&A functionality.

## Features
- ✅ Document Upload (TXT files)
- ✅ Question Answering using RoBERTa
- ✅ Sentiment Analysis
- ✅ Answer Paraphrasing
- ✅ Suggested Questions
- ✅ Chat Interface

## Setup

```powershell
cd E:\Legal-AI_Project-main\Legal-AI_Project-main\streamlit_project_v1

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Differences from v2 (Current)
- **v1**: Basic Q&A only
- **v2**: Includes NER, Clause Classification, Risk Analysis, PDF support, Tabbed Dashboard
