import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="AI Research 2-Pager", layout="centered")

st.title("🧠 AI-Powered Company 2-Pager Generator")
st.markdown("Generate a professional research brief for any company using public data and AI summarization.")

company_name = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")
brave_api_key = st.secrets.get("BRAVE_API_KEY", "your-brave-api-key")  # Replace with your actual API key

def search_brave(query):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": brave_api_key
    }
    params = {"q": query, "count": 5}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        results = response.json().get("web", {}).get("results", [])
        return [r["url"] for r in results]
    return []

def scrape_and_summarize(url):
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")
        text = soup.get_text()
        return text.strip().replace("\n", " ").replace("  ", " ")[:2000]
    except Exception:
        return ""

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split("\n"):
        pdf.multi_cell(0, 10, line)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name

if st.button("Generate 2-Pager"):
    if not company_name or not industry:
        st.warning("Please enter both company name and industry.")
    else:
        sections = {
            "1. Business Overview": "",
            "2. Key Products and Business Model": "",
            "3. Key Financial Metrics": "",
            "4. Fundraising History": "",
            "5. Industry Outlook (Headwinds & Tailwinds)": "",
            "6. Private Credit Use Case": ""
        }

        for section in sections:
            query = f"{company_name} {industry} {region} {section}"
            urls = search_brave(query)
            texts = [scrape_and_summarize(url) for url in urls]
            combined_text = "\n\n".join(texts)
            summary = combined_text[:1000] if combined_text else "Information not available or could not be retrieved."
            sections[section] = summary

        report = "**Research Report: {} in the {} Industry in {}**\n\n".format(company_name, industry, region)
        for header, body in sections.items():
            report += f"**{header}:**\n{body}\n\n"

        st.text_area("Generated 2-Pager", report, height=500)

        try:
            pdf_file_path = generate_pdf(report)
            with open(pdf_file_path, "rb") as file:
                st.download_button("📥 Download as PDF", file, file_name=f"{company_name}_2pager.pdf")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")