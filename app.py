import os
import tempfile
import textwrap
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from openai import OpenAI
import fitz  # PyMuPDF
from urllib.parse import urlparse

# -- SETUP --
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
BRAVE_API_KEY = st.secrets["BRAVE_API_KEY"]
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
PREFERRED_DOMAINS = ("crunchbase", "techcrunch", "yahoo", "bloomberg", "reuters", "dealstreetasia", "finextra")

# -- HELPERS --
def brave_search(query, count=8):
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": count}
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
    results = response.json().get("web", {}).get("results", []) if response.ok else []
    urls, domains = [], set()
    for r in results:
        url = r.get("url", "")
        domain = urlparse(url).netloc.lower()
        if any(p in domain for p in PREFERRED_DOMAINS) and domain not in domains:
            urls.append(url)
            domains.add(domain)
    return urls

def scrape_text(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if not resp.ok or "cloudflare" in resp.text.lower():
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        return text.replace("\xa0", " ").replace("\n", " ")[:2500]
    except Exception:
        return ""

def extract_teaser(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
        doc = fitz.open(tmp.name)
        return " ".join(page.get_text() for page in doc)[:3000]
    except Exception:
        return ""

def gpt_report(full_context, company, industry, region):
    prompt = f"""
    You are a research analyst writing a professional investment briefing on the company "{company}" in the "{industry}" sector, operating in "{region}".
    Write a crisp, factual 2-page styled research report with these 6 sections:
    1. Business Overview
    2. Key Products and Business Model
    3. Financial & Operating Metrics
    4. Fundraising History
    5. Industry Outlook (Headwinds & Tailwinds)
    6. Private Credit Use Case (if applicable)

    Keep it factual and clear. Use bullet points where helpful. Do NOT speculate or assume anything not stated in the context below.

    ## SOURCE DATA:
    {full_context}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": textwrap.dedent(prompt)}],
        temperature=0.2,
        max_tokens=1800
    )
    return response.choices[0].message.content.strip()

def generate_pdf(text, company):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.multi_cell(0, 10, f"{company} – Company Research Brief", align="C")
    pdf.ln(4)
    pdf.set_font("Arial", "", 12)
    for para in text.split("\n"):
        pdf.multi_cell(0, 7, para.strip())
        pdf.ln(1)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# -- UI --
st.set_page_config(page_title="AI Research Brief", layout="centered")
st.title("📊 AI-Powered Company Research Brief")

with st.form("research_form"):
    company = st.text_input("🔹 Company Name")
    industry = st.text_input("🔹 Industry")
    region = st.text_input("🌍 Region")
    teaser = st.file_uploader("📎 Upload Teaser Deck (optional, PDF)", type=["pdf"])
    submit = st.form_submit_button("Generate Report")

if submit and company and industry:
    with st.spinner("🔍 Collecting data & drafting report..."):
        queries = [
            f"{company} {industry} business overview {region}",
            f"{company} {industry} products model",
            f"{company} {industry} revenue user metrics",
            f"{company} {industry} fundraising history investors",
            f"{industry} market outlook {region}",
            f"{company} private credit venture debt receivables"
        ]
        sources = " ".join(scrape_text(url) for q in queries for url in brave_search(q))
        teaser_text = extract_teaser(teaser) if teaser else ""
        full_context = f"{sources}\n\n[From Teaser Deck]:\n{teaser_text}" if teaser_text else sources

        report_text = gpt_report(full_context, company, industry, region)
        pdf_path = generate_pdf(report_text, company)

    st.success("✅ Report generated successfully!")
    st.markdown(report_text)
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Download Report as PDF", f, file_name=f"{company}_ResearchBrief.pdf", mime="application/pdf")
