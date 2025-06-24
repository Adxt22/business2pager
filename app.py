
import streamlit as st
import openai
import requests
from fpdf import FPDF
import tempfile
import os

# Config
BRAVE_API_KEY = "BSA0WLjSjc8kFYJ3NpQ-U-R2UP1S9o1"
openai.api_key = os.getenv("OPENAI_API_KEY")

def fetch_brave_snippets(company, industry, region):
    query = f"{company} {industry} {region} site:crunchbase.com OR site:{company.lower()}.com"
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count=5&spellcheck=1&source=web"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    response = requests.get(url, headers=headers)
    results = response.json().get("web", {}).get("results", [])
    snippets = "\n\n".join([r.get("description", "") for r in results])
    return snippets if snippets else "No relevant data found."

st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered")
st.title("🚀 AI-Powered Startup 2-Pager")

company = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

if st.button("Generate 2-Pager Report"):
    if not company or not industry or not region:
        st.warning("Please enter Company, Industry, and Region.")
    else:
        with st.spinner("Searching and generating report..."):
            try:
                context = fetch_brave_snippets(company, industry, region)
                prompt = f"""
You are a professional investment analyst. Based on the data below, write a clear, factual, and structured 2-page report on the startup '{company}' in the '{industry}' industry in '{region}'.

Context from web search:
"""
{context}
"""

Structure the report as:
1. Business Overview
2. Key Products and Business Model
3. Key Financial Metrics (if available)
4. Key Operating Metrics (if available)
5. Fundraising History
6. Industry Outlook – Headwinds & Tailwinds
7. Private Credit Use Case – applicability, risks, collateral
"""

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a professional startup analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1800
                )

                report = response["choices"][0]["message"]["content"]
                st.success("✅ Report Generated")
                st.text_area("Generated Report", report, height=500)

                # PDF Export (Unicode-safe)
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in report.split('\n'):
                    safe_line = line.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, safe_line)

                filename = f"{company} - Intro.pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    tmp_file.flush()
                    with open(tmp_file.name, "rb") as f:
                        st.download_button(
                            label="📄 Download PDF",
                            data=f,
                            file_name=filename,
                            mime="application/pdf"
                        )

            except Exception as e:
                st.error(f"Error: {e}")
