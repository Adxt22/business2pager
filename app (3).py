
import streamlit as st
import openai
import requests
from fpdf import FPDF
import os

st.set_page_config(page_title="Startup 2-Pager Generator", page_icon="🚀")
st.markdown("## 🚀 Startup 2-Pager Generator")

openai.api_key = st.secrets["OPENAI_API_KEY"]
brave_api_key = st.secrets["BRAVE_API_KEY"]

def search_with_brave(query):
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count=5"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": brave_api_key
    }
    response = requests.get(url, headers=headers)
    results = response.json()
    snippets = [r.get("description", "") for r in results.get("web", {}).get("results", [])]
    return "\n".join(snippets)

def generate_report(context, company, industry, region):
    prompt = f"""Use only the following context to write a factual 2-page research summary on {company} in the {industry} industry ({region}).
Do not assume or invent anything. Structure it as:
1. Business Overview
2. Key Products and Business Model
3. Financial Metrics (if any)
4. Operating Metrics (if any)
5. Fundraising and Investor Info (if any)
6. Industry Outlook (Headwinds/Tailwinds)
7. Private Credit Use Case (if applicable)
\nContext:\n{context}"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message["content"]

def export_pdf(report_text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in report_text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    pdf.output(filename)

company = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

if st.button("Generate 2-Pager Report"):
    with st.spinner("Searching the web and generating report..."):
        query = f"{company} {industry} {region}"
        context = search_with_brave(query)
        report = generate_report(context, company, industry, region)
        st.text_area("📄 Generated 2-Pager Report:", value=report, height=400)
        filename = f"{company} - Intro.pdf"
        export_pdf(report, filename)
        with open(filename, "rb") as f:
            st.download_button("📥 Download Report as PDF", f, file_name=filename, mime="application/pdf")
