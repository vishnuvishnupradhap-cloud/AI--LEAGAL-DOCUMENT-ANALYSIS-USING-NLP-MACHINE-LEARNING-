import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

def get_db_connection():
    """Establish and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        content TEXT,
        entities TEXT,
        clauses TEXT,
        risk_analysis TEXT
    )
    ''')
    
    # Create chat_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def save_document(filename, content, entities, clauses, risk_analysis):
    """Save an analyzed document to the database and return its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documents (filename, content, entities, clauses, risk_analysis)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        filename, 
        content, 
        json.dumps(entities) if entities else None, 
        json.dumps(clauses) if clauses else None, 
        json.dumps(risk_analysis) if risk_analysis else None
    ))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def get_all_documents():
    """Retrieve all saved documents (basic info only)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_date FROM documents ORDER BY upload_date DESC')
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]

def search_documents(query):
    """Search documents by filename, content, or entities."""
    conn = get_db_connection()
    cursor = conn.cursor()
    like_query = f"%{query}%"
    cursor.execute('''
        SELECT id, filename, upload_date 
        FROM documents 
        WHERE filename LIKE ? OR content LIKE ? OR entities LIKE ?
        ORDER BY upload_date DESC
    ''', (like_query, like_query, like_query))
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]

def find_related_documents_by_property(properties, exclude_filename=None):
    """Find historical documents that mention matching properties."""
    if not properties:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    related_docs = []
    seen_ids = set()
    
    for prop in properties:
        # Simple LIKE logic: if the entities JSON string contains the property
        like_query = f"%{prop}%"
        
        if exclude_filename:
            cursor.execute('''
                SELECT *
                FROM documents 
                WHERE entities LIKE ? AND filename != ?
                ORDER BY upload_date DESC
            ''', (like_query, exclude_filename))
        else:
            cursor.execute('''
                SELECT *
                FROM documents 
                WHERE entities LIKE ?
                ORDER BY upload_date DESC
            ''', (like_query,))
            
        docs = cursor.fetchall()
        for doc in docs:
            if doc['id'] not in seen_ids:
                doc_dict = dict(doc)
                doc_dict['entities'] = json.loads(doc_dict['entities']) if doc_dict['entities'] else None
                doc_dict['clauses'] = json.loads(doc_dict['clauses']) if doc_dict['clauses'] else None
                doc_dict['risk_analysis'] = json.loads(doc_dict['risk_analysis']) if doc_dict['risk_analysis'] else None
                related_docs.append(doc_dict)
                seen_ids.add(doc['id'])
                
    conn.close()
    return related_docs

def get_document_by_id(doc_id):
    """Retrieve a full document with its analysis data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = cursor.fetchone()
    conn.close()
    if doc:
        doc_dict = dict(doc)
        doc_dict['entities'] = json.loads(doc_dict['entities']) if doc_dict['entities'] else None
        doc_dict['clauses'] = json.loads(doc_dict['clauses']) if doc_dict['clauses'] else None
        doc_dict['risk_analysis'] = json.loads(doc_dict['risk_analysis']) if doc_dict['risk_analysis'] else None
        return doc_dict
    return None

def delete_document(doc_id):
    """Delete a document and its associated chat history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE document_id = ?', (doc_id,))
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()

def save_chat_message(document_id, role, content, msg_id=None):
    """Save a chat message associated with a document.
       msg_id is added as optional since it isn't in schema but can be passed for compatibility.
    """
    if not document_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (document_id, role, content)
        VALUES (?, ?, ?)
    ''', (document_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(document_id):
    """Retrieve chat history for a specific document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content, timestamp, id 
        FROM chat_history 
        WHERE document_id = ? 
        ORDER BY id ASC
    ''', (document_id,))
    history = cursor.fetchall()
    conn.close()
    return [dict(msg) for msg in history]
