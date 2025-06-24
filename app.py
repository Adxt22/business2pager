import streamlit as st
import requests
from fpdf import FPDF
import re

# Set your Brave Search API key
BRAVE_API_KEY = "BSA0WLjSjc8kFYJ3NpQ-U-R2UP1S9o1"

# Clean text to avoid UnicodeEncodeError
def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

# Search function using Brave API
def search_brave(query):
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    response = requests.get(
        f"https://api.search.brave.com/res/v1/web/search?q={query}&count=10",
        headers=headers
    )
    if response.status_code == 200:
        results = response.json().get("web", {}).get("results", [])
        return "\n".join([r.get("description", "") for r in results])
    else:
        return f"Search error: {response.status_code}"

# Report Generator
def generate_report(company, industry, region):
    query = f"{company} {industry} {region}"
    raw_content = search_brave(query)
    content = clean_text(raw_content)

    # Simulate structured report (can be made dynamic)
    report = f"""Research Report: {company} in the {industry} Industry in {region}

1. Business Overview:
{content.split('.')[0]}

2. Key Products and Business Model:
{content.split('.')[1]}

3. Key Financial Metrics:
{content.split('.')[2] if len(content.split('.')) > 2 else 'Data not available'}

4. Fundraising History:
{content.split('.')[3] if len(content.split('.')) > 3 else 'Data not available'}

5. Industry Outlook (Headwinds & Tailwinds):
{content.split('.')[4] if len(content.split('.')) > 4 else 'Data not available'}

6. Private Credit Use Case:
Based on the company’s operations, a private credit or venture debt fund may explore structured debt or revenue-based financing tied to receivables, expansion, or cash flow cycles.
"""
    return report

# PDF Writer
def generate_pdf(report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in report.split('\n'):
        pdf.multi_cell(0, 10, clean_text(line))
    pdf_path = "/mnt/data/Alif_Report_Cleaned.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Streamlit Web UI
st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered", page_icon="🚀")
st.markdown("<h1 style='text-align: center;'>🚀 Startup 2-Pager Generator</h1>", unsafe_allow_html=True)

with st.form("input_form"):
    company = st.text_input("Enter Company Name", "")
    industry = st.text_input("Enter Industry", "")
    region = st.text_input("Enter Region", "")
    submitted = st.form_submit_button("Generate 2-Pager Report")

if submitted and company and industry and region:
    with st.spinner("Generating report..."):
        report = generate_report(company, industry, region)
        st.text_area("📄 Generated Report", value=report, height=400)
        pdf_file_path = generate_pdf(report)
        st.success("✅ Report generated successfully!")
        st.download_button("📥 Download PDF", data=open(pdf_file_path, "rb"), file_name="2pager.pdf", mime="application/pdf")
