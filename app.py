
    import streamlit as st
    import requests
    import openai
    from urllib.parse import urlparse
    from fpdf import FPDF
    import os

    st.set_page_config(page_title="🧠 2-Pager Generator for Fund Managers", page_icon="💼", layout="centered")
    st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .stButton>button {
        border-radius: 10px;
        background-color: #004080;
        color: white;
        font-weight: bold;
    }
    .stDownloadButton>button {
        background-color: #1a8cff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("💼 Professional 2-Pager Generator for Fund Managers")
    st.caption("Powered by Brave Search + OpenAI | Tailored for private credit and venture investors")

    # Load API keys from environment or Streamlit secrets
    OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    BRAVE_KEY = st.secrets.get("BRAVE_API_KEY") or os.getenv("BRAVE_API_KEY")

    if not OPENAI_KEY or not BRAVE_KEY:
        st.error("Missing API keys. Please configure OPENAI_API_KEY and BRAVE_API_KEY.")
        st.stop()

    openai.api_key = OPENAI_KEY

    def brave_search(query, num_results=10):
        url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count={num_results}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_KEY
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])

    def filter_results(results):
        preferred = ["crunchbase", "techcrunch", "techinasia", "dealstreetasia", "yourstory"]
        filtered = []
        for r in results:
            domain = urlparse(r.get("url", "")).netloc.lower()
            if any(p in domain for p in preferred) or "blog" in domain or "news" in domain:
                filtered.append(r)
        return filtered[:6]

    def build_context(results):
        context = []
        for r in results:
            title = r.get("title", "")
            desc = r.get("description", "")
            url = r.get("url", "")
            context.append(f"TITLE: {title}\nURL: {url}\nSNIPPET: {desc}")
        return "\n---\n".join(context)

    def generate_report(context, company, industry, region):
        prompt = f"""Act as a private markets investment associate preparing an internal 2-pager briefing note on the startup {company}, operating in the {industry} industry in {region}. 
Use only the context below (web snippets) to write a detailed memo. Be factual, concise, and structured. 

Avoid generalizations. If any sections are missing data, mention 'Not available'. Use a professional tone.

Context:
{context}

Required sections:
1. Company Overview (founding year, HQ, founders, mission)
2. Products & Business Model (what they sell, how they make money)
3. Financial & Operating Metrics (revenue, GMV, users, growth)
4. Fundraising History (rounds, investors, amounts)
5. Industry & Regional Outlook (macro tailwinds/headwinds)
6. Private Credit Use Case (instrument, returns, security, covenants)
7. Key Questions for Management (for intro call)
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2400
        )
        return response.choices[0].message.content.strip()

    def save_pdf(text, file_path):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        for line in text.split('\n'):
            pdf.multi_cell(0, 8, line)
        pdf.output(file_path)

    with st.form("input_form"):
        col1, col2, col3 = st.columns(3)
        company = col1.text_input("🔍 Company Name", placeholder="e.g. Alif Group")
        industry = col2.text_input("🏭 Industry", placeholder="e.g. Fintech Lending")
        region = col3.text_input("🌍 Region", placeholder="e.g. Central Asia")

        submitted = st.form_submit_button("Generate 2-Pager")

    if submitted:
        if not all([company, industry, region]):
            st.warning("Please fill all input fields to proceed.")
            st.stop()

        with st.spinner("Searching web and generating memo..."):
            query = f"{company} {industry} {region}"
            try:
                raw_results = brave_search(query, 10)
            except Exception as e:
                st.error(f"Brave API error: {e}")
                st.stop()

            results = filter_results(raw_results)
            if not results:
                st.error("Insufficient quality data found. Try broadening your search.")
                st.stop()

            context = build_context(results)
            report = generate_report(context, company, industry, region)
            st.success("2-Pager Ready ✅")
            st.text_area("📄 Generated 2-Pager", report, height=500)

            pdf_name = f"{company} - Intro.pdf"
            save_pdf(report, f"/mnt/data/{pdf_name}")
            with open(f"/mnt/data/{pdf_name}", "rb") as pdf_file:
                st.download_button("📥 Download PDF", pdf_file, file_name=pdf_name, mime="application/pdf")
