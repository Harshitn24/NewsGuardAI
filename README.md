# 🛡️ NewsGuard AI

**AI-Powered News Credibility Analysis**

This project analyzes news articles and assigns a credibility score using web search, web scraping, heuristics, and Google Gemini LLM.

---

## **Features**

* Input news text via Streamlit UI
* Fetch relevant articles using Google Custom Search API
* Scrape article content with BeautifulSoup
* Heuristic credibility scoring based on trusted sources and content
* AI-based stance detection, confidence scoring, and explanation using **Google Gemini**
* Download analysis report as JSON

---

## **Technologies**

* **Frontend:** Streamlit
* **Web Search:** Google Custom Search API
* **Web Scraping:** Requests + BeautifulSoup
* **LLM / AI Model:** Google Gemini 2.5 (via Agno)
* **Agent Framework:** Agno

  > *Future options:* Vertex AI SDK or LangChain
* **Environment / Utilities:** Python-dotenv, urllib.parse, time

---

## **Setup Instructions**

1. **Clone the repository:**

```bash
git clone https://github.com/Harshitn24/NewsGuardAI.git
cd NewsGuardAI
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Setup environment variables** in a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_custom_search_id
GEMINI_API_KEY=your_gemini_api_key
```

4. **Run the Streamlit app:**

```bash
streamlit run main.py
```

5. Open your browser and navigate to `http://localhost:8501` to use the app.

---

## **Usage**

1. Enter the text of a news article in the input box.
2. Click **Analyze Now**.
3. View verdict (Reliable / Unreliable / Mixed / Not Enough Evidence), credibility score, explanation, and top sources.
4. Download the report as JSON using the download button.

---

## **Requirements**

* Python 3.10+
* Streamlit
* Requests
* BeautifulSoup4
* python-dotenv
* pydantic
* google-api-python-client
* agno

---

## **Future Improvements**

* Replace heuristic scoring with fully agent-driven workflow
* Integrate Vertex AI SDK or LangChain for advanced agent orchestration
* Add visual dashboards for analysis summary
