import os
import tempfile
import textwrap
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import openai
import fitz  # PyMuPDF
from urllib.parse import urlparse
from collections import OrderedDict

# --- CONFIGURATION ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
BRAVE_API_KEY = st.secrets["BRAVE_API_KEY"]
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
PREFERRED_DOMAINS = ("crunchbase", "techcrunch", "yahoo", "bloomberg", "reuters", "dealstreetasia", "finextra")

# --- HELPER FUNCTIONS ---

def brave_search(query, count=8):
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {"q": query, "count": count}
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
    results = response.json().get("web", {}).get("results", []) if response.ok else []
    urls = []
    seen_domains = set()
    for r in results:
        url = r.get("url", "")
        domain = urlparse(url).netloc.lower()
        if any(p in domain for p in PREFERRED_DOMAINS) and domain not in seen_domains:
            urls.append(url)
            seen_domains.add(domain)
    return urls

def scrape_text(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if not resp.ok or "cloudflare" in resp.text.lower():
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        text = text.replace("\xa0", " ").replace("\n", " ")
        return text[:2500]
    except Exception:
        return ""

def extract_teaser_text(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        doc = fitz.open(tmp_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text[:3000]
    except Exception:
        return ""

def gpt_summarize(section, text):
    prompt = f"""
    You are a research analyst. Write a concise, factual summary for the section: {section}
    based only on the information below. Use bullet points where appropriate.

    ### Input:
    {text}
    """
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": textwrap.dedent(prompt)}],
        temperature=0.3,
        max_tokens=400
    )
    return res.choices[0].message.content.strip()

def generate_pdf(report_dict, company):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"{company} – Company Research Brief", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    for title, body in report_dict.items():
        pdf.set_font("Arial", "B", 13)
        pdf.multi_cell(0, 10, f"\n{title}")
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, body)
        pdf.ln(2)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# --- STREAMLIT UI ---
st.set_page_config(page_title="Startup Research Generator", layout="centered")
st.title("📊 AI-Generated Company Research Report")

with st.form("input_form"):
    c1, c2 = st.columns(2)
    company = c1.text_input("Company Name")
    industry = c2.text_input("Industry")
    region = st.text_input("Region (optional)")
    teaser_file = st.file_uploader("Optional: Upload Teaser Deck (PDF only)", type=["pdf"])
    submitted = st.form_submit_button("Generate Report")

if submitted and company and industry:
    with st.spinner("🔍 Gathering data..."):
        section_queries = {
            "1. Business Overview": f"{company} {industry} overview {region}",
            "2. Key Products & Business Model": f"{company} {industry} business model products",
            "3. Financial & Operating Metrics": f"{company} {industry} revenue users financials",
            "4. Fundraising History": f"{company} fundraising investment rounds capital raised",
            "5. Industry Outlook": f"{industry} trends 2024 {region}",
            "6. Private Credit Use Case": f"{company} revenue-based lending or private credit deal"
        }

        raw_inputs = {}
        for section, query in section_queries.items():
            urls = brave_search(query)
            combined_text = " ".join(scrape_text(u) for u in urls)
            raw_inputs[section] = combined_text

        if teaser_file:
            teaser_text = extract_teaser_text(teaser_file)
            for section in raw_inputs:
                raw_inputs[section] += f"\n\nFrom Teaser Deck:\n{teaser_text}"

    with st.spinner("✍️ Generating summaries..."):
        report = OrderedDict()
        for section, text in raw_inputs.items():
            summary = gpt_summarize(section, text if text else "No data available.")
            report[section] = summary

    st.success("✅ Report ready.")
    for section, content in report.items():
        st.markdown(f"### {section}\n{content}\n")

    pdf_path = generate_pdf(report, company)
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Download PDF", f, file_name=f"{company}_2pager.pdf")
