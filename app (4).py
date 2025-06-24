
import streamlit as st
import requests
import openai
from urllib.parse import urlparse
from fpdf import FPDF
import os

st.set_page_config(page_title="Startup 2‑Pager Generator", page_icon="🚀", layout="centered")
st.title("🚀 Fund‑Ready Startup 2‑Pager Generator")

# Load API keys from Streamlit secrets or environment variables
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
BRAVE_KEY = st.secrets.get("BRAVE_API_KEY") or os.getenv("BRAVE_API_KEY")

if not OPENAI_KEY or not BRAVE_KEY:
    st.error("Please set OPENAI_API_KEY and BRAVE_API_KEY in Streamlit secrets.")
    st.stop()

openai.api_key = OPENAI_KEY

# --- Helper Functions ---
def brave_search(query, num_results=10):
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count={num_results}"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_KEY
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("web", {}).get("results", [])

def filter_results(results):
    preferred = ["crunchbase.com", "techcrunch.com", "techinasia.com"]
    filtered = []
    for r in results:
        domain = urlparse(r.get("url", "")).netloc.lower()
        if any(p in domain for p in preferred) or domain.endswith(".com"):
            filtered.append(r)
    return filtered[:5]

def build_context(results):
    parts = []
    for r in results:
        title = r.get("title", "")
        desc = r.get("description", "")
        url = r.get("url", "")
        parts.append(f"TITLE: {title}\nURL: {url}\nSNIPPET: {desc}\n")
    return "\n---\n".join(parts)

def generate_report(context, company, industry, region):
    prompt = f"""You are a senior investment analyst. Using ONLY the factual snippets below, draft a thorough two‑page memo on {company} ({industry}, {region}). Do not fabricate data.

=== Context ===
{context}
=== End Context ===

## Output Structure
1. Company Snapshot
2. Products & Business Model
3. Key Financial & Operating Metrics
4. Fundraising & Capital Structure
5. Industry & Regional Outlook
6. Private Credit / Venture Debt Thesis
7. Key Questions for Management
"""
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2200
    )
    return resp.choices[0].message.content.strip()

def save_pdf(text, file_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in text.split('\n'):
        pdf.multi_cell(0, 8, line)
    pdf.output(file_path)

# --- UI ---
c1, c2, c3 = st.columns(3)
company = c1.text_input("Company Name")
industry = c2.text_input("Industry")
region = c3.text_input("Region")

if st.button("Generate 2‑Pager"):
    if not all([company, industry, region]):
        st.warning("Fill all fields.")
        st.stop()
    with st.spinner("Gathering web data..."):
        query = f"{company} {industry} {region}"
        try:
            raw_results = brave_search(query, 10)
        except Exception as e:
            st.error(f"Brave API error: {e}")
            st.stop()

        results = filter_results(raw_results)
        if not results:
            st.error("No relevant search results found.")
            st.stop()

        context = build_context(results)
        report = generate_report(context, company, industry, region)
        st.success("Report Ready!")
        st.text_area("2‑Pager Draft", report, height=500)

        pdf_name = f"{company} - Intro.pdf"
        save_pdf(report, pdf_name)
        with open(pdf_name, "rb") as pdf_file:
            st.download_button("Download PDF", pdf_file, file_name=pdf_name, mime="application/pdf")
