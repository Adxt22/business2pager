import streamlit as st
import requests
from fpdf import FPDF
import os

# Set page config
st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered")

st.markdown(
    "<h1 style='text-align: center;'>🚀 Startup 2-Pager Generator</h1>",
    unsafe_allow_html=True
)

company = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

def search_brave(company, industry, region, api_key):
    query = f"{company} {industry} {region}"
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": 10}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        results = response.json().get("web", {}).get("results", [])
        return [r["title"] + ": " + r["url"] + " - " + r.get("description", "") for r in results]
    return ["No relevant web results found."]

def generate_report(company, industry, region, search_results):
    report = f"""
**Research Report: {company} in the {industry} Industry in {region}**

**1. Business Overview:**
{search_results[0] if search_results else 'No detailed overview found.'}

**2. Key Products and Business Model:**
{search_results[1] if len(search_results) > 1 else 'Details not found in public sources.'}

**3. Key Financial Metrics:**
{search_results[2] if len(search_results) > 2 else 'Not publicly disclosed or limited.'}

**4. Fundraising History:**
{search_results[3] if len(search_results) > 3 else 'Funding information unavailable.'}

**5. Industry Outlook (Headwinds & Tailwinds):**
{search_results[4] if len(search_results) > 4 else 'General industry trends can be found online.'}

**6. Private Credit Use Case:**
Based on the company's operations, a private credit or venture debt fund may explore structured debt or revenue-based financing tied to the company's receivables, expansion, or cash flow cycles. Assess covenant strength, runway, and burn rate if available.
"""
    return report

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    pdf_path = "/mnt/data/Startup_2Pager_Report.pdf"
    pdf.output(pdf_path)
    return pdf_path

if st.button("Generate 2-Pager Report"):
    if company and industry and region:
        with st.spinner("Searching and generating report..."):
            brave_api_key = os.getenv("BRAVE_API_KEY", "BSA0WLjSjc8kFYJ3NpQ-U-R2UP1S9o1")
            search_results = search_brave(company, industry, region, brave_api_key)
            report = generate_report(company, industry, region, search_results)
            st.markdown(report)
            pdf_file_path = generate_pdf(report)
            with open(pdf_file_path, "rb") as f:
                st.download_button("📄 Download Report as PDF", f, file_name="2Pager_Report.pdf")
    else:
        st.error("Please enter all fields.")
