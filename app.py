
import streamlit as st

from pdf_reader import extract_text
from analyzer import analyze_resume

st.set_page_config(
    page_title="AI Resume Analyzer",
    layout="wide"
)

st.title("📄 AI Resume Analyzer")
st.write("Offline Resume Analysis using Ollama")

uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf"]
)

if uploaded_file:

    with st.spinner("Reading Resume..."):

        resume = extract_text(uploaded_file)

    st.success("Resume Loaded Successfully")

    if st.button("Analyze Resume"):

        with st.spinner("Analyzing..."):

            result = analyze_resume(resume)

        st.markdown(result)

        st.download_button(
            "Download Report",
            result,
            file_name="resume_analysis.txt"
        )


