# ── app.py ──────────────────────────────────────────────────────────────
import os, re, tempfile, requests, textwrap
from collections import OrderedDict
from urllib.parse import urlparse

import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF
import openai

# ── CONFIG ──────────────────────────────────────────────────────────────
openai.api_key   = st.secrets["OPENAI_API_KEY"]
BRAVE_API_KEY    = st.secrets["BRAVE_API_KEY"]
BRAVE_ENDPOINT   = "https://api.search.brave.com/res/v1/web/search"
PREFERRED_SITES  = ("crunchbase", "techcrunch", "reuters", "bloomberg", "yahoo", 
                    "dealstreetasia", "finextra", "businesswire", "techinasia")

# ── HELPERS ─────────────────────────────────────────────────────────────
def brave_search(q: str, n: int = 10):
    """Return a list of unique, high-quality URLs from Brave search."""
    headers = {"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"}
    resp    = requests.get(BRAVE_ENDPOINT, headers=headers, params={"q": q, "count": n})
    results = resp.json().get("web", {}).get("results", []) if resp.ok else []
    urls, seen_domains = [], set()
    for r in results:
        url, dom = r["url"], urlparse(r["url"]).netloc.lower()
        if any(p in dom for p in PREFERRED_SITES) and dom not in seen_domains:
            urls.append(url); seen_domains.add(dom)
    return urls[:5]

def scrape_text(url: str, chars: int = 3500):
    """Extract & clean plain text from a web page."""
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        text = re.sub(r"\s+", " ", text)
        return text[:chars]
    except Exception:
        return ""

def dedupe_sentences(text: str, max_sents=20):
    """Remove near-duplicate sentences, keep order."""
    seen, out = set(), []
    for sent in re.split(r"(?<=[.!?]) +", text):
        s = sent.strip()
        if 30 < len(s) < 300 and s.lower() not in seen:
            out.append(s); seen.add(s.lower())
        if len(out) >= max_sents:
            break
    return " ".join(out)

def gpt_summarize(section_title: str, raw_text: str):
    """Call GPT to craft a concise, professional paragraph/bullets."""
    prompt = textwrap.dedent(f"""
        You are a senior investment analyst. Summarise the following
        information into a concise, factual section titled '{section_title}'.
        Use bullet points where helpful.  Avoid fluff or marketing language.

        ### Raw info
        {raw_text[:3000]}
    """)
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300
    )
    return resp.choices[0].message.content.strip()

def make_pdf(report: OrderedDict, company: str):
    """Create a nicely formatted PDF and return temp file path."""
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 10, f"{company} – Research Brief", align="C")
    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    for header, body in report.items():
        pdf.set_font("Arial", "B", 12); pdf.multi_cell(0, 8, header)
        pdf.set_font("Arial", "", 11);  pdf.multi_cell(0, 8, body); pdf.ln(3)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# ── STREAMLIT UI ────────────────────────────────────────────────────────
st.title("📑 Professional 2-Pager Generator")

with st.form("input"):
    c1, c2, c3 = st.columns(3)
    company = c1.text_input("Company")
    industry = c2.text_input("Industry")
    region   = c3.text_input("Region")
    submitted = st.form_submit_button("🔍 Generate Report")

if submitted and company and industry:
    with st.spinner("Collecting sources…"):
        queries = {
            "Business Overview"                    : f"{company} {industry} overview {region}",
            "Products & Business Model"            : f"{company} product business model",
            "Financial & Operating Metrics"        : f"{company} revenue users funding",
            "Fundraising History"                  : f"{company} funding rounds investors",
            "Industry & Regional Outlook"          : f"{industry} market trend {region}",
            "Private Credit / Venture Debt Thesis" : f"{company} debt facility sukuk revenue financing"
        }
        raw_sections = {}
        for section, q in queries.items():
            urls   = brave_search(q)
            text   = " ".join(scrape_text(u) for u in urls)
            raw_sections[section] = dedupe_sentences(text)

    with st.spinner("Drafting summary…"):
        final_report = OrderedDict()
        for sec, raw in raw_sections.items():
            final_report[sec] = gpt_summarize(sec, raw) if raw else "No public data available."

    st.success("Report ready!")
    for h, b in final_report.items():
        st.markdown(f"### {h}\n{b}\n")

    pdf_path = make_pdf(final_report, company)
    with open(pdf_path, "rb") as f:
        st.download_button("⬇️ Download PDF", f, file_name=f"{company}_2pager.pdf", mime="application/pdf")
