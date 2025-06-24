
import streamlit as st
import openai
import os
from fpdf import FPDF

st.set_page_config(page_title="Startup 2-Pager Generator", layout="centered")

st.title("🚀 Startup 2-Pager Generator")

company_name = st.text_input("Enter Company Name", "")
industry = st.text_input("Enter Industry", "")
region = st.text_input("Enter Region", "")

if st.button("Generate 2-Pager Report"):
    with st.spinner("Generating..."):
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")

            client = openai.OpenAI()
            context = f"""
            Research the company "{company_name}" operating in the "{industry}" industry in "{region}".
            Generate a factual, well-structured 2-page summary covering:
            - Business Overview (founding year, HQ, founders, mission, market position)
            - Key Products and Business Model
            - Key Operating and Financial Metrics (if publicly available)
            - Funding History
            - Industry & Regional Outlook
            - Potential Use Cases for Private Credit or Venture Debt (if applicable)

            Only use information available online and do not hallucinate or assume details.
            Cite specific facts where relevant. Keep it professional.
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an analyst generating factual business reports for investors."},
                    {"role": "user", "content": context}
                ]
            )

            report = response.choices[0].message.content

            st.subheader("Generated Report")
            st.text_area("Report", report, height=600)

            # Export to PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in report.split("\n"):
                pdf.multi_cell(0, 10, line)

            filename = f"{company_name} - Intro.pdf"
            pdf_path = f"/mnt/data/{filename}"
            pdf.output(pdf_path)
            st.success("PDF Report Generated!")
            st.download_button("Download PDF", data=open(pdf_path, "rb").read(), file_name=filename, mime="application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
