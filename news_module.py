import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

def fetch_gpt4_news_insights(document_text: str, api_key: str):
    """
    Uses OpenAI's GPT-4 to analyze a document, extract optimal news search queries,
    fetches live RSS news, and uses GPT-4 again to contextualize the news.
    """
    try:
        from openai import OpenAI
    except ImportError:
        return {"error": "OpenAI library not installed. Add 'openai' to requirements."}
        
    if not api_key:
        return {"error": "No OpenAI API key provided."}
        
    client = OpenAI(api_key=api_key)
    
    # 1. Ask GPT-4 to extract a targeted search query for current legal news
    try:
        query_prompt = f"Analyze the following legal text snippet and determine the primary legal domain and jurisdiction (e.g., 'California Employment Law'). Return ONLY a 2-3 word search query that would be optimal for finding recent legal news related to this document. Text: {document_text[:3000]}"
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # use latest efficient gpt-4 model
            messages=[{"role": "user", "content": query_prompt}],
            temperature=0.1
        )
        search_query = completion.choices[0].message.content.strip()
        search_query = search_query.replace('"', '')
    except Exception as e:
        return {"error": f"Error communicating with OpenAI for query generation: {str(e)}"}
        
    if not search_query or len(search_query) < 3:
        search_query = "National Legal News"
        
    # 2. Fetch live news using Google News RSS
    encoded_query = urllib.parse.quote(f"{search_query} law legal")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    articles = []
    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            for item in items[:5]: # Top 5 articles
                articles.append({
                    "title": item.title.text if item.title else "No Title",
                    "link": item.link.text if item.link else "#",
                    "pubDate": item.pubDate.text if item.pubDate else "No Date",
                    "description": item.description.text if getattr(item, 'description', None) else ""
                })
    except Exception as e:
         return {"error": f"Error fetching news RSS feed: {str(e)}"}
         
    if not articles:
        return {"error": f"No recent news found for query '{search_query}'."}
        
    # 3. Use GPT-4 to summarize and contextualize the news articles
    try:
        news_text = "\\n\\n".join([f"Title: {a['title']}\\nPublished: {a['pubDate']}" for a in articles])
        
        insight_prompt = f"You are a legal analyst. Here are the latest news headlines related to '{search_query}':\\n\\n{news_text}\\n\\nBased on these headlines, provide a 2-paragraph 'Live News Insight' summary explaining the current legal landscape and how these recent developments might relate to the topic of the document. Write in a clear, professional tone."
        
        insight_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": insight_prompt}],
            temperature=0.3
        )
        insight_summary = insight_completion.choices[0].message.content.strip()
    except Exception as e:
        insight_summary = "GPT-4 was unable to generate a summary for the news articles at this time."

    return {
        "search_query": search_query,
        "insight_summary": insight_summary,
        "articles": articles
    }
