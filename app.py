
import streamlit as st
import openai
from fpdf import FPDF
import os

st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered")

st.title("🚀 Startup 2-Pager Generator")

company_name = st.text_input("Enter Company Name")
industry = st.text_input("Enter Industry")
region = st.text_input("Enter Region")

if st.button("Generate 2-Pager Report") and company_name and industry and region:
    with st.spinner("Generating..."):

        openai.api_key = os.getenv("OPENAI_API_KEY")

        try:
            search_prompt = f"""Search online and collect facts from official company sources and credible media about the company named "{company_name}" in the "{industry}" industry based in the "{region}" region. Then write a structured 2-page professional business research brief in markdown format with these sections:

## 1. Business Overview
## 2. Key Products and Business Model
## 3. Financial Metrics (if available)
## 4. Operating Metrics (if available)
## 5. Fundraising and Investors (if available)
## 6. Industry Outlook (tailwinds/headwinds)
## 7. Potential Use of Private Credit or Venture Debt (if applicable)

Only use factual information. Do not assume anything that cannot be verified online. Format output cleanly with bullets where needed."""

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a business analyst trained in summarizing companies using factual web data."},
                    {"role": "user", "content": search_prompt}
                ]
            )
            content = response.choices[0].message.content

            st.markdown("### Generated Report")
            st.markdown(content)

            # Export as PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in content.split("\n"):
                pdf.multi_cell(0, 10, line)
            filename = f"{company_name} - Intro.pdf"
            pdf.output(filename)
            with open(filename, "rb") as f:
                st.download_button("📄 Download PDF", f, file_name=filename, mime="application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
