import streamlit as st
import PyPDF2
import anthropic
import os

# --- CONFIG ---
API_KEY = "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"  # paste your key
BASE_FOLDER = "D:\\concall_transcripts"

# --- COMPANY DEFINITIONS ---
COMPANIES = {
    "GE Vernova T&D India": {
        "folder": "GE_Vernova",
        "quarters": ["Nov '25", "Feb '26", "May '26", "Aug '26"]
    },
    "Nuvama Wealth Management": {
        "folder": "Nuvama",
        "quarters": ["Q1", "Q2", "Q3", "Q4"]  # update with actual quarter names
    },
    "ideaForge Technology": {
        "folder": "ideaForge",
        "quarters": ["Q1", "Q2", "Q3", "Q4"]  # update with actual quarter names
    }
}

# --- LOAD TRANSCRIPTS ---
@st.cache_data
def load_company_transcripts(company_name):
    company = COMPANIES[company_name]
    folder_path = os.path.join(BASE_FOLDER, company["folder"])
    transcripts = {}
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            quarter_label = filename.replace(".txt", "")
            transcripts[quarter_label] = text
    
    return transcripts

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
st.divider()

# Company selector
company = st.selectbox(
    "Select company:",
    options=list(COMPANIES.keys())
)

# Show available quarters
folder_path = os.path.join(BASE_FOLDER, COMPANIES[company]["folder"])
available_files = [f.replace(".pdf", "") for f in sorted(os.listdir(folder_path)) if f.endswith(".pdf")]
st.caption(f"Available transcripts: {' | '.join(available_files)}")

st.divider()

# Preset questions
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
    "What guidance has management given for the next quarter or year?",
]

if 'question' not in st.session_state:
    st.session_state.question = ''

for i, q in enumerate(presets):
    if i % 2 == 0:
        if col1.button(q, key=f"btn_{i}"):
            st.session_state.question = q
    else:
        if col2.button(q, key=f"btn_{i}"):
            st.session_state.question = q

st.divider()

# Free text input
question = st.text_input("Or type your own question:", value=st.session_state.question)

if st.button("Ask", type="primary") and question:
    with st.spinner(f"Analysing {company} transcripts..."):
        transcripts = load_company_transcripts(company)
        answer = ask_claude(question, transcripts, company)
    
    st.markdown(f"### {company} — Answer")
    st.markdown(answer)
    st.divider()
    st.caption(f"Source: {company} earnings call transcripts — {' | '.join(available_files)}")