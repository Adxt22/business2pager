
import streamlit as st
import requests
from fpdf import FPDF
import tempfile
from bs4 import BeautifulSoup

# --- CONFIG ---
BRAVE_API_KEY = "BSA0WLjSjc8kFYJ3NpQ-U-R2UP1S9o1"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

# --- FUNCTIONS ---
def search_web(company, industry, region):
    query = f"{company} {industry} {region} site:crunchbase.com OR site:techcrunch.com OR site:finextra.com OR site:businesswire.com OR site:reuters.com OR site:bloomberg.com OR site:dealstreetasia.com OR site:finance.yahoo.com"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": 5}
    res = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
    if res.status_code == 200:
        return res.json().get("web", {}).get("results", [])
    return []

def clean_text(text):
    return text.replace("\xa0", " ").replace("\n", " ").strip()

def generate_summary(results, company):
    report = f"**Research Report: {company}**\n\n"
    sections = {
        "1. Business Overview": "",
        "2. Key Products and Business Model": "",
        "3. Key Financial Metrics": "",
        "4. Fundraising History": "",
        "5. Industry Outlook (Headwinds & Tailwinds)": "",
        "6. Private Credit Use Case": "Based on the company’s operations, a private credit or venture debt fund may explore structured debt or revenue-based financing tied to receivables, expansion, or cash flow cycles."
    }
    for result in results:
        text = f"- {result['title']}: {result['url']}"
        for section in sections:
            if section in ["1. Business Overview", "2. Key Products and Business Model"]:
                sections[section] += text + "\n"
            elif section == "3. Key Financial Metrics" and "raise" in result["title"].lower():
                sections[section] += text + "\n"
            elif section == "4. Fundraising History" and "fund" in result["title"].lower():
                sections[section] += text + "\n"
            elif section == "5. Industry Outlook (Headwinds & Tailwinds)" and any(k in result["title"].lower() for k in ["trend", "future", "outlook"]):
                sections[section] += text + "\n"
    for k, v in sections.items():
        report += f"{k}:\n{v}\n\n"
    return report

def generate_pdf(report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in report.split("\n"):
        pdf.multi_cell(0, 10, clean_text(line))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name

# --- UI ---
st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered")
st.title("🚀 Startup 2-Pager Generator")
company = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

if st.button("Generate 2-Pager Report"):
    if company and industry and region:
        with st.spinner("Searching and compiling information..."):
            search_results = search_web(company, industry, region)
            report = generate_summary(search_results, company)
            st.text_area("Generated 2-Pager Report", report, height=400)
            pdf_file_path = generate_pdf(report)
            with open(pdf_file_path, "rb") as f:
                st.download_button("📥 Download PDF", data=f, file_name="2pager.pdf", mime="application/pdf")
    else:
        st.warning("Please fill in all fields to generate the report.")
