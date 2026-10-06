import streamlit as st
import anthropic
import os

# --- CONFIG ---
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
TRANSCRIPT_FOLDER = "."

COMPANIES = {
    "GE Vernova T&D India": "GE_Vernova",
    "Nuvama Wealth Management": "Nuvama",
    "ideaForge Technology": "ideaForge"
}

# --- LOAD TRANSCRIPTS ---
@st.cache_data
def load_company_transcripts(company_name):
    prefix = COMPANIES[company_name]
    transcripts = {}
    
    for filename in sorted(os.listdir(TRANSCRIPT_FOLDER)):
        if filename.startswith(prefix) and filename.endswith(".txt"):
            path = os.path.join(TRANSCRIPT_FOLDER, filename)
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            quarter_label = filename.replace(prefix + "_", "").replace(".txt", "")
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
st.markdown("Built by Jagrav Manwani | CFA Level I | Independent Equity Research")
st.divider()

company = st.selectbox(
    "Select company:",
    options=list(COMPANIES.keys())
)

transcripts = load_company_transcripts(company)
available = list(transcripts.keys())

if not transcripts:
    st.error(f"No transcripts found for {company}. Check file naming.")
    st.stop()

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

question = st.text_input("Or type your own question:", value=st.session_state.question)

if st.button("Ask", type="primary") and question:
    with st.spinner(f"Analysing {company} transcripts..."):
        answer = ask_claude(question, transcripts, company)
    
    st.markdown(f"### {company} — Answer")
    st.markdown(answer)
    st.divider()
    st.caption(f"Source: {company} earnings call transcripts — {' | '.join(available)}")
