import streamlit as st
import os
from pathlib import Path
import tempfile
from typing import Optional
import PyPDF2
import json

# Import our custom components
from agents.summarizer import SummarizerAgent
from agents.red_flag import RedFlagAgent
from agents.summary_gen import ExecutiveSummaryAgent
from utils.text_splitter import DocumentSplitter
from utils.faq_bot import FAQBot
from utils.output_parser import OutputParser
from config import GOOGLE_API_KEY, GEMINI_MODEL

# Set page config
st.set_page_config(
    page_title="SaaS Terms Simplifier",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_text' not in st.session_state:
    st.session_state.processed_text = None
if 'summaries' not in st.session_state:
    st.session_state.summaries = None
if 'red_flags' not in st.session_state:
    st.session_state.red_flags = None
if 'chunks' not in st.session_state:
    st.session_state.chunks = None
if 'faq_bot' not in st.session_state:
    st.session_state.faq_bot = None
if 'summary_type' not in st.session_state:
    st.session_state.summary_type = "non-technical"
if 'executive_summary' not in st.session_state:
    st.session_state.executive_summary = None
if 'input_text' not in st.session_state:
    st.session_state.input_text = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def process_text(text: str, saas_name: str, api_key: str):
    """Process the input text through our pipeline."""
    try:
        # Reset analysis state
        st.session_state.analysis_complete = False
        st.session_state.summaries = None
        st.session_state.red_flags = None
        st.session_state.executive_summary = None
        st.session_state.faq_bot = None
        
        # Initialize components
        splitter = DocumentSplitter()
        summarizer = SummarizerAgent(api_key)
        red_flag_detector = RedFlagAgent(api_key)
        executive_summarizer = ExecutiveSummaryAgent(api_key)
        faq_bot = FAQBot(api_key)
        
        # Split text into chunks
        chunks = splitter.split_text(text)
        st.session_state.chunks = chunks
        
        # Process each chunk
        summaries = []
        red_flags = []
        
        for chunk in chunks:
            # Generate summary
            summary = summarizer.summarize(
                chunk["text"],
                summary_type=st.session_state.summary_type,
                saas_name=saas_name
            )
            summaries.append(summary)
            
            # Detect red flags
            flags = red_flag_detector.detect_red_flags(
                chunk["text"],
                saas_name=saas_name
            )
            if flags.get("red_flags"):
                red_flags.extend(flags["red_flags"])
        
        # Generate executive summary
        executive_summary = executive_summarizer.generate_summary(
            text,
            saas_name=saas_name,
            summary_type=st.session_state.summary_type
        )
        
        # Initialize FAQ bot
        faq_bot.add_documents(chunks)
        
        # Store results in session state
        st.session_state.summaries = summaries
        st.session_state.red_flags = red_flags
        st.session_state.executive_summary = executive_summary
        st.session_state.faq_bot = faq_bot
        st.session_state.analysis_complete = True
        
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        # Reset all analysis states
        st.session_state.processed_text = None
        st.session_state.summaries = None
        st.session_state.red_flags = None
        st.session_state.chunks = None
        st.session_state.faq_bot = None
        st.session_state.executive_summary = None
        st.session_state.analysis_complete = False
        raise e  # Re-raise the exception to be caught by the caller

def main():
    st.title("🧾 SaaS Terms Simplifier")
    st.markdown("""
    Upload your SaaS Terms & Conditions document or paste the text below to:
    - Get a plain English summary
    - Identify potential red flags
    - Generate an executive summary
    - Chat with an AI assistant about the terms
    """)

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        saas_name = st.text_input("SaaS Product Name (optional)")
        
        summary_type = st.radio(
            "Summary Type",
            ["Non-technical", "Technical"],
            index=0
        )
        st.session_state.summary_type = summary_type.lower()

    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Upload/Paste",
        "📚 Summary",
        "🚨 Red Flags",
        "💬 Chat",
        "📤 Export"
    ])

    with tab1:
        input_method = st.radio(
            "Choose input method:",
            ["Upload PDF", "Paste Text"],
            horizontal=True
        )

        if input_method == "Upload PDF":
            uploaded_file = st.file_uploader(
                "Upload your Terms & Conditions PDF",
                type=['pdf']
            )
            if uploaded_file:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        text = extract_text_from_pdf(tmp_file.name)
                        if text:
                            st.session_state.text_content = text
                            st.success("File uploaded successfully!")
                            
                            # Add some spacing
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Center the analyze button
                            col1, col2, col3 = st.columns([2, 1, 2])
                            with col2:
                                analyze_button = st.button(
                                    "🔍 Analyze",
                                    type="primary",
                                    use_container_width=True,
                                    key="analyze_button_pdf"
                                )
                            
                            # Messages container for better alignment
                            message_container = st.container()
                            with message_container:
                                # Center align messages
                                if analyze_button:
                                    if not GOOGLE_API_KEY:
                                        col1, col2, col3 = st.columns([1, 2, 1])
                                        with col2:
                                            st.error("Google API key is not configured. Please check your .env file.")
                                    else:
                                        # Center the spinner and success message
                                        container = st.container()
                                        with container:
                                            st.markdown(
                                                """
                                                <div style="display: flex; justify-content: center; align-items: center; margin: 1rem 0;">
                                                    <div style="text-align: center; width: 100%;">
                                                """,
                                                unsafe_allow_html=True
                                            )
                                            
                                            with st.spinner("Analyzing document..."):
                                                try:
                                                    process_text(text, saas_name, GOOGLE_API_KEY)
                                                    if st.session_state.analysis_complete:
                                                        st.markdown(
                                                            """
                                                            <div style="text-align: center; margin-top: 1rem;">
                                                                <p style="color: #00CC00; padding: 10px; border-radius: 5px; background-color: #1E1E1E;">
                                                                    ✅ Analysis completed successfully!
                                                                </p>
                                                            </div>
                                                            """,
                                                            unsafe_allow_html=True
                                                        )
                                                except Exception:
                                                    # Error is already displayed by process_text
                                                    pass
                                            
                                            st.markdown(
                                                """
                                                    </div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                            )
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
        else:
            # Initialize session state for text input if not exists
            if 'text_content' not in st.session_state:
                st.session_state.text_content = ""

            # Text area for input
            text_input = st.text_area(
                "Paste your Terms & Conditions here",
                value=st.session_state.text_content,
                height=300,
                key="text_area",
                on_change=lambda: st.session_state.update(text_content=st.session_state.text_area)
            )

            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Center the analyze button
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                analyze_button = st.button(
                    "🔍 Analyze",
                    type="primary",
                    disabled=not bool(st.session_state.text_content.strip()),
                    use_container_width=True,
                    key="analyze_button"
                )
            
            # Messages container for better alignment
            message_container = st.container()
            with message_container:
                # Center align messages
                if analyze_button and st.session_state.text_content.strip():
                    if not GOOGLE_API_KEY:
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.error("Google API key is not configured. Please check your .env file.")
                    else:
                        # Center the spinner and success message
                        container = st.container()
                        with container:
                            st.markdown(
                                """
                                <div style="display: flex; justify-content: center; align-items: center; margin: 1rem 0;">
                                    <div style="text-align: center; width: 100%;">
                                """,
                                unsafe_allow_html=True
                            )
                            
                            with st.spinner("Analyzing document..."):
                                try:
                                    process_text(st.session_state.text_content, saas_name, GOOGLE_API_KEY)
                                    if st.session_state.analysis_complete:
                                        st.markdown(
                                            """
                                            <div style="text-align: center; margin-top: 1rem;">
                                                <p style="color: #00CC00; padding: 10px; border-radius: 5px; background-color: #1E1E1E;">
                                                    ✅ Analysis completed successfully!
                                                </p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                except Exception:
                                    # Error is already displayed by process_text
                                    pass
                            
                            st.markdown(
                                """
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

    with tab2:
        if not st.session_state.analysis_complete:
            st.info("Please upload a document and click 'Analyze Document' to view the summary.")
        elif st.session_state.summaries and st.session_state.executive_summary:
            st.subheader("Document Summary")
            
            # Display executive summary
            st.markdown("### Executive Summary")
            st.markdown(st.session_state.executive_summary["summary"])
            
            # Display detailed summaries
            st.markdown("### Detailed Section Summaries")
            for i, summary in enumerate(st.session_state.summaries):
                with st.expander(f"Section {i+1}"):
                    st.markdown(summary["summary"])

    with tab3:
        if not st.session_state.analysis_complete:
            st.info("Please upload a document and click 'Analyze Document' to view red flags.")
        elif st.session_state.red_flags:
            st.subheader("Red Flags")
            
            # Group flags by severity
            high_flags = [f for f in st.session_state.red_flags if f["severity"] == "High"]
            medium_flags = [f for f in st.session_state.red_flags if f["severity"] == "Medium"]
            low_flags = [f for f in st.session_state.red_flags if f["severity"] == "Low"]
            
            # Display flags by severity
            if high_flags:
                st.markdown("### 🔴 High Severity")
                for flag in high_flags:
                    with st.expander(flag["category"]):
                        st.markdown(f"**Clause:** {flag['clause']}")
                        st.markdown(f"**Explanation:** {flag['explanation']}")
                        st.markdown(f"**Impact:** {flag['impact']}")
            
            if medium_flags:
                st.markdown("### 🟡 Medium Severity")
                for flag in medium_flags:
                    with st.expander(flag["category"]):
                        st.markdown(f"**Clause:** {flag['clause']}")
                        st.markdown(f"**Explanation:** {flag['explanation']}")
                        st.markdown(f"**Impact:** {flag['impact']}")
            
            if low_flags:
                st.markdown("### 🟢 Low Severity")
                for flag in low_flags:
                    with st.expander(flag["category"]):
                        st.markdown(f"**Clause:** {flag['clause']}")
                        st.markdown(f"**Explanation:** {flag['explanation']}")
                        st.markdown(f"**Impact:** {flag['impact']}")

    with tab4:
        if not st.session_state.analysis_complete:
            st.info("Please upload a document and click 'Analyze Document' to start chatting.")
        elif st.session_state.faq_bot:
            st.subheader("Chat with the Terms")
            
            # Initialize chat history if not exists
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []

            # Display chat history
            for q, a in st.session_state.chat_history:
                # User message with custom styling
                st.markdown(
                    f"""
                    <div style="
                        background-color: #2E4B73;
                        padding: 10px;
                        border-radius: 10px;
                        margin: 5px 0;
                        max-width: 80%;
                        margin-left: auto;
                        margin-right: 10px;
                    ">
                        <strong>You:</strong><br>{q}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Assistant message with custom styling
                st.markdown(
                    f"""
                    <div style="
                        background-color: #0E1117;
                        border: 1px solid #2E4B73;
                        padding: 10px;
                        border-radius: 10px;
                        margin: 5px 0;
                        max-width: 80%;
                        margin-right: auto;
                        margin-left: 10px;
                    ">
                        <strong>Assistant:</strong><br>{a}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Add some space between chat history and input
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Chat interface
            chat_placeholder = st.empty()
            with chat_placeholder.container():
                # Create columns for input and buttons
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    question = st.text_input(
                        "Type your question here...",
                        key=f"chat_input_{len(st.session_state.chat_history)}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    send = st.button("💬 Send", use_container_width=True)
                
                with col3:
                    if st.session_state.chat_history:
                        clear = st.button("🗑️ Clear", use_container_width=True)
                        if clear:
                            st.session_state.chat_history = []
                            st.experimental_rerun()

                if send and question:
                    try:
                        with st.spinner("Thinking..."):
                            response = st.session_state.faq_bot.ask_question(question)
                            st.session_state.chat_history.append((question, response["answer"]))
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error getting response: {str(e)}")
                        st.experimental_rerun()

    with tab5:
        if not st.session_state.analysis_complete:
            st.info("Please upload a document and click 'Analyze Document' to export results.")
        elif st.session_state.summaries and st.session_state.red_flags and st.session_state.executive_summary:
            st.subheader("Export Results")
            
            # Create export data
            export_data = {
                "executive_summary": st.session_state.executive_summary,
                "summaries": st.session_state.summaries,
                "red_flags": st.session_state.red_flags,
                "metadata": {
                    "saas_name": saas_name,
                    "summary_type": st.session_state.summary_type,
                    "model": GEMINI_MODEL,
                    "timestamp": st.session_state.analysis_complete
                }
            }
            
            # Export as JSON
            json_str = json.dumps(export_data, indent=2)
            st.markdown("### Export Options")
            
            # Add export buttons in a cleaner layout
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📄 Download as JSON",
                    data=json_str,
                    file_name="saas_terms_analysis.json",
                    mime="application/json",
                    key="json_download"
                )
            
            with col2:
                # Generate markdown content
                try:
                    parser = OutputParser()
                    markdown_content = parser.generate_markdown(export_data)
                    st.download_button(
                        label="📝 Download as Markdown",
                        data=markdown_content,
                        file_name="saas_terms_analysis.md",
                        mime="text/markdown",
                        key="md_download"
                    )
                except Exception as e:
                    st.error(f"Error generating Markdown: {str(e)}")
            
            with col3:
                # Generate and download PDF
                try:
                    parser = OutputParser()
                    pdf_bytes = parser.generate_pdf(export_data)
                    st.download_button(
                        label="📚 Download as PDF",
                        data=pdf_bytes,
                        file_name="saas_terms_analysis.pdf",
                        mime="application/pdf",
                        key="pdf_download"
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
        else:
            st.error("Analysis results are incomplete. Please try analyzing the document again.")

if __name__ == "__main__":
    main() 