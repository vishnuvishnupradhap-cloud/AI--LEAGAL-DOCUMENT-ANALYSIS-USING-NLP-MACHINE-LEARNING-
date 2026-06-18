import streamlit as st
import json
from io import StringIO
from textblob import TextBlob
from predict import run_prediction
from paraphrase import paraphrase
from news_module import fetch_gpt4_news_insights

# Page Config
st.set_page_config(page_title="Legal AI Chatbot", layout="wide")

# Custom CSS for chat style
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #2b313e;
    }
    .assistant-message {
        background-color: #1c1f26;
    }
    .sentiment-positive {
        color: #4ade80;
        font-weight: bold;
    }
    .sentiment-negative {
        color: #f87171;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Helper Function: Sentiment Analysis
def get_sentiment(text):
    if not text:
        return "Neutral"
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

def get_sentiment_color(sentiment):
    if sentiment == "Positive":
        return "sentiment-positive"
    elif sentiment == "Negative":
        return "sentiment-negative"
    return "sentiment-neutral"

import PyPDF2

# Sidebar: File Upload
with st.sidebar:
    st.title("⚙️ Settings")
    st.text_input("OpenAI API Key (for Live News)", type="password", key="openai_api_key", help="Enter your OpenAI API key to enable GPT-4 powered Real-Time Legal News Insights.")
    st.markdown("---")
    
    st.title("📁 Document Upload")
    uploaded_file = st.file_uploader("Upload a Contract (TXT/PDF)", type=['txt', 'pdf'])
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            document_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    document_text += text + "\n"
        else:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            document_text = stringio.read()
            
        st.session_state['document_text'] = document_text
        st.success("Document loaded successfully!")
        
        with st.expander("View Document Content"):
            st.text(document_text[:1000] + "...")
    else:
        if 'document_text' in st.session_state:
            del st.session_state['document_text']

    st.markdown("---")
    st.subheader("💡 Suggested Questions")
    
    # Predefined questions list (cleaned up from file)
    questions_list = [
        "What is the contract name?",
        "Who are the parties that signed the contract?",
        "What is the agreement date of the contract?",
        "What is the date when the contract is effective?",
        "What date will the contract's initial term expire?",
        "What is the renewal term after the initial term expires?",
        "What is the notice period required to terminate renewal?",
        "Which state/country's law governs the interpretation of the contract?",
        "Can a party terminate this contract without cause?",
        "What are the terms about right of termination?",
        "Is consent or notice required if the contract is assigned to a third party?",
        "What are the terms for revenue and profit sharing?",
        "What are the terms about intellectual property created by one party?",
        "Does the contract contain a license granted by one party to its counterparty?",
        "Is a party subject to obligations after the termination or expiration of a contract?"
    ]
    
    # Use a selectbox for cleaner UI than many buttons
    selected_question = st.selectbox("Choose a question:", [""] + questions_list)
    
    if st.button("Ask Selected Question"):
        if selected_question:
            st.session_state['auto_ask'] = selected_question

# Main Chat Interface
st.title("🤖 Legal AI Assistant")

# Create tabs for Chat and News Insights
tab1, tab2 = st.tabs(["💬 Q&A Chat", "📰 Live News Insights"])

with tab1:
    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Handle Auto-Ask (from Sidebar)
    if 'auto_ask' in st.session_state:
        prompt = st.session_state['auto_ask']
        del st.session_state['auto_ask'] # Consume the event
    else:
        # Standard Chat Input
        prompt = st.chat_input("Ask a question about the contract...")
    
    if prompt:
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
    
        # Check if document is loaded
        if 'document_text' not in st.session_state:
            response_text = "⚠️ Please upload a document first using the sidebar."
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.markdown(response_text)
        else:
            # Generate Response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing document..."):
                    try:
                        # Run Prediction
                        predictions_list = run_prediction([prompt], st.session_state['document_text'], 'marshmellow77/roberta-base-cuad', n_best_size=3)
                        
                        answer_data = []
                        # Check if we got results for our question (first item in the list)
                        if predictions_list and len(predictions_list) > 0:
                            top_answers = predictions_list[0]
                            
                            for pred in top_answers:
                                answer_data.append({
                                    "text": pred['answer'],
                                    "prob": round(pred['score'] * 100, 1),
                                    "sentiment": get_sentiment(pred['answer'])
                                })
                        
                        if not answer_data:
                             st.markdown("I couldn't find a confident answer in the document.")
                             st.session_state.messages.append({"role": "assistant", "content": "I couldn't find a confident answer in the document."})
                        else:
                            # Construct a formatted response
                            final_response = "Here are the top findings:\n\n"
                            for i, ans in enumerate(answer_data):
                                color_class = get_sentiment_color(ans['sentiment'])
                                final_response += f"**{i+1}.** {ans['text']}  \n"
                                final_response += f"*Confidence: {ans['prob']}% | Sentiment: <span class='{color_class}'>{ans['sentiment']}</span>*  \n\n"
                            
                            st.markdown(final_response, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": final_response})
                            
                            # Add "Explain" buttons (Streamlit buttons inside chat are tricky, using expander instead)
                            with st.expander("💡 Explain / Paraphrase Top Answer"):
                                 with st.spinner("Paraphrasing..."):
                                     try:
                                         explanation = paraphrase(answer_data[0]['text'])
                                         # paraphrase returns a list usually
                                         if isinstance(explanation, list):
                                             st.markdown(f"_{explanation[0]}_")
                                         else:
                                             st.markdown(f"_{explanation}_")
                                     except Exception as e:
                                         st.error(f"Could not paraphrase: {e}")

                    except Exception as e:
                        error_msg = f"An error occurred during analysis: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Display Chat History at the bottom
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

with tab2:
    st.header("📰 Real-Time Legal News Insights")
    st.write("Leverage GPT-4 to dynamically evaluate your legal document and fetch up-to-the-minute jurisdictional news related to its contents.")
    
    if 'document_text' not in st.session_state:
        st.info("👈 Please upload a legal document first.")
    elif not st.session_state.get('openai_api_key'):
        st.error("⚠️ Please enter your OpenAI API key in the sidebar to enable live news integration.")
    else:
        if st.button("Fetch Live News Insights"):
            with st.spinner("GPT-4 is analyzing the document for context and fetching recent legal news..."):
                news_result = fetch_gpt4_news_insights(st.session_state['document_text'], st.session_state['openai_api_key'])
                
                if "error" in news_result:
                    st.error(news_result['error'])
                else:
                    st.subheader(f"🔍 Search Context: `{news_result['search_query']}`")
                    
                    st.markdown("### 🤖 GPT-4 Insight Summary")
                    st.info(news_result['insight_summary'])
                    
                    st.markdown("### 🗞️ Latest Related Articles")
                    for article in news_result['articles']:
                        with st.container():
                            st.markdown(f"**[{article['title']}]({article['link']})**")
                            st.caption(f"🗓️ {article['pubDate']}")
                            if article['description']:
                                st.markdown(f"<small>{article['description']}</small>", unsafe_allow_html=True)
                            st.divider()
