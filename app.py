import streamlit as st
import openai
from fpdf import FPDF
import os

# Set your OpenAI API key (ensure this is stored securely in production)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_report(company_name, industry, region):
    prompt = f"""
Generate a factual and professional 2-page research report about the company '{company_name}' in the '{industry}' industry located in the '{region}' region.
The report should include:
1. Business Overview (what the company does)
2. Key Products and Business Model
3. Key Financial Metrics (if available)
4. Key Operating Metrics (if available)
5. Fundraising History
6. Industry Outlook (headwinds/tailwinds)
7. Use case for Private Credit if applicable
Use only factual and verifiable sources. Do not make up any data.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # use gpt-4 if you have access
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def export_to_pdf(content, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    pdf.output(filename)

# Streamlit UI
st.title("🚀 Startup 2-Pager Generator")

company_name = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

if st.button("Generate 2-Pager Report"):
    if company_name and industry and region:
        with st.spinner("Generating report..."):
            report = generate_report(company_name, industry, region)
            if not report.startswith("Error"):
                st.success("Report generated successfully!")
                st.text_area("Generated Report", report, height=400)
                filename = f"{company_name} - Intro.pdf"
                export_to_pdf(report, filename)
                with open(filename, "rb") as f:
                    st.download_button(
                        label="📄 Download Report as PDF",
                        data=f,
                        file_name=filename,
                        mime="application/pdf"
                    )
            else:
                st.error(report)
    else:
        st.warning("Please fill in all fields before generating.")
