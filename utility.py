# app.py
import os
import json
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# Agno + Google Gemini
from agno.agent import Agent
from agno.models.google import Gemini

# Google Search API
from googleapiclient.discovery import build

# -----------------------------------------------------------------------------
# Load env variables
# -----------------------------------------------------------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")     # Programmable Search
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")       # CSE ID
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")     # Gemini
GEMINI_MODEL = "gemini-2.5-flash-lite"

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="FactCheck API", version="1.0")

class AnalyzeRequest(BaseModel):
    text: str

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def search_google(query: str, max_results: int = 5):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=max_results).execute()
        results = []
        for item in res.get("items", []):
            results.append({
                "title": item.get("title"),
                "href": item.get("link"),
                "body": item.get("snippet")
            })
        return results
    except Exception as e:
        print(f"[Error] Google search failed: {e}")
        return []


def scrape_url(url: str):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta = meta_tag["content"].strip() if meta_tag and "content" in meta_tag.attrs else ""
        text = " ".join(p.get_text() for p in soup.find_all("p"))[:3000]
        return {"title": title, "meta": meta, "text": text}
    except Exception as e:
        print(f"[Error] Failed to scrape {url}: {e}")
        return {"title": "", "meta": "", "text": ""}


def domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def find_credibility_score(domain: str, scraped: dict) -> int:
    domain = domain.lower()
    trusted_domains = {
        "thehindu.com": 90, "indianexpress.com": 88, "hindustantimes.com": 85,
        "timesofindia.indiatimes.com": 85, "ndtv.com": 83, "indiatoday.in": 85,
        "thewire.in": 82, "scroll.in": 80, "business-standard.com": 82,
        "livemint.com": 82, "reuters.com": 95, "bbc.com": 92,
        "nytimes.com": 90, "theguardian.com": 88, "aljazeera.com": 85,
        "wikipedia.org": 75,
    }
    heuristic_score = trusted_domains.get(domain, 50)
    if domain.endswith(".gov") or domain.endswith(".nic.in"):
        heuristic_score += 30
    elif domain.endswith(".edu") or domain.endswith(".ac.in"):
        heuristic_score += 25
    if any(s in domain for s in ["medium.com", ".blog", "wordpress.com"]):
        heuristic_score -= 25
    if any(s in domain for s in ["reddit.com", "quora.com", "facebook.com", "twitter.com"]):
        heuristic_score -= 35
    if scraped.get("meta"):
        heuristic_score += 5
    if len(scraped.get("text", "")) > 1200:
        heuristic_score += 10
    elif len(scraped.get("text", "")) < 200:
        heuristic_score -= 10
    return max(0, min(100, heuristic_score))


# -----------------------------------------------------------------------------
# FactCheck Pipeline
# -----------------------------------------------------------------------------
def run_factcheck_pipeline(claim: str, max_search: int = 6):
    search_results = search_google(claim, max_results=max_search)
    evidences = []
    for r in search_results:
        url = r.get("href")
        if not url:
            continue
        scraped = scrape_url(url)
        domain = domain_from_url(url)
        score = find_credibility_score(domain, scraped)
        evidences.append({
            "url": url,
            "title": scraped.get("title") or r.get("title"),
            "meta": scraped.get("meta") or r.get("body"),
            "text": scraped.get("text"),
            "domain": domain,
            "credibility": score,
        })
        time.sleep(0.3)

    top4 = sorted(evidences, key=lambda e: e["credibility"], reverse=True)[:4]
    evidence_str = "\n\n".join(
        [f"- Title: {e['title']}\n  URL: {e['url']}\n  Credibility: {e['credibility']}\n  Snippet: {e['meta'] or e['text'][:400]}"
        for e in evidences]
    )

    # print("[DEBUG]: Till This.......")
    final_prompt = f"""
        You are a fact-checking assistant.

        Claim: "{claim}"

        Evidence collected:
        {evidence_str}

        Task:
        1. Based on the evidence, give a final stance: supports / refutes / mixture / insufficient.
        2. Provide a confidence score (0-100).
        3. Write a short 3-5 line explanation.
        4. Highlight which top 3 sources were most influential.

        Output Requirements:
        - Respond ONLY with a single valid JSON object.
        - Do NOT use Markdown formatting, code blocks, or backticks.
        - Do NOT include any text before or after the JSON.
        - The response MUST strictly pass json.loads() without modification.

        JSON Keys: stance, confidence, explanation, top_sources
        """


    model = Gemini(id=GEMINI_MODEL, api_key=GEMINI_API_KEY)
    agent = Agent(model=model, tools=[], markdown=False)

    res = agent.run(final_prompt)
    try:
        # print(res.content)
        parsed = json.loads(res.content)
        # print("[DEBUG]: ",parsed)
    except Exception as e:
        # print(e)
        parsed = {
            "stance": "insufficient",
            "confidence": 50,
            "explanation": str(e),
            "top_sources": [s["url"] for s in top4],
        }

    return parsed, top4