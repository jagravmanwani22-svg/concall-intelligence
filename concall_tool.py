import streamlit as st
import anthropic
import os
from datetime import datetime
from PyPDF2 import PdfReader

# --- CONFIG ---
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
FOLDER = "."

# Optional: nicer names for the dropdown. Anything not listed here
# is shown using its file prefix, with underscores turned into spaces.
DISPLAY_NAMES = {
    "GE_Vernova": "GE Vernova T&D India",
    "Nuvama": "Nuvama Wealth Management",
    "ideaForge": "ideaForge Technology",
}

# --- FILE HANDLING ---
def read_file(path):
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def quarter_sort_key(label):
    # Sorts labels like Nov25, Feb26, Aug26 in date order
    try:
        return datetime.strptime(label, "%b%y")
    except ValueError:
        return datetime.min

def discover_companies():
    # Finds every file named Company_MonYY.pdf or Company_MonYY.txt
    companies = {}
    for filename in os.listdir(FOLDER):
        if not filename.endswith((".txt", ".pdf")):
            continue
        name = filename.rsplit(".", 1)[0]
        if "_" not in name:
            continue
        prefix, quarter = name.rsplit("_", 1)
        companies.setdefault(prefix, {})[quarter] = filename
    return companies

@st.cache_data
def load_transcripts(prefix, files):
    ordered = sorted(files, key=lambda item: quarter_sort_key(item[0]))
    return {q: read_file(os.path.join(FOLDER, f)) for q, f in ordered}

# --- QUERY CLAUDE ---
def ask_claude(question, transcripts, company_name):
    client = anthropic.Anthropic(api_key=API_KEY)
    combined = ""
    for quarter, text in transcripts.items():
        combined += f"\n\n--- {quarter} EARNINGS CALL ---\n{text}"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""You are an equity research analyst assistant.
You have access to earnings call transcripts for {company_name}.

{combined}

Answer the question based only on what is in the transcripts.
Always cite which quarter you are referencing.
Be specific — use numbers and direct references where available.

Question: {question}"""
        }]
    )
    return message.content[0].text

# --- UI ---
st.set_page_config(page_title="Concall Intelligence Tool", layout="wide")

st.title("Concall Intelligence Tool")
st.subheader("AI-powered earnings call analysis for Indian listed companies")
st.markdown("Built by Jagrav Manwani | CFA Level I | Independent Equity Research")
st.divider()

companies = discover_companies()
if not companies:
    st.error("No transcripts found. Name files like Company_Aug26.pdf")
    st.stop()

def display_name(prefix):
    return DISPLAY_NAMES.get(prefix, prefix.replace("_", " "))

prefix = st.selectbox(
    "Select company:",
    options=sorted(companies.keys(), key=lambda p: display_name(p).lower()),
    format_func=display_name,
)
company = display_name(prefix)

files = tuple(sorted(companies[prefix].items()))
transcripts = load_transcripts(prefix, files)
available = list(transcripts.keys())
st.caption(f"Available transcripts: {' | '.join(available)}")
st.divider()

st.markdown("**Quick questions:**")
col1, col2 = st.columns(2)

presets = [
    "What has management said about revenue growth and outlook?",
    "How have margins trended and what drives the change?",
    "What are the key growth drivers management has highlighted?",
    "What risks has management flagged across quarters?",
    "How has the order book or AUM evolved?",
    "What has management said about competition?",
    "How has cash flow and working capital been discussed?",
    "What guidance has management given for next quarter or year?",
]

if "question" not in st.session_state:
    st.session_state.question = ""

for i, q in enumerate(presets):
    col = col1 if i % 2 == 0 else col2
    if col.button(q, key=f"btn_{i}"):
        st.session_state.question = q

st.divider()

question = st.text_input("Or type your own question:", value=st.session_state.question)

if st.button("Ask", type="primary") and question:
    with st.spinner(f"Analysing {company} transcripts..."):
        answer = ask_claude(question, transcripts, company)

    st.markdown(f"### {company} — Answer")
    st.markdown(answer)
    st.divider()
    st.caption(f"Source: {company} earnings call transcripts — {' | '.join(available)}")
