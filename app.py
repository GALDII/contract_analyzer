import streamlit as st
from core.analyzer import analyze_contract
from core.document_parser import parse_document
from chatbot.vector_store import get_pinecone_retriever
from chatbot.chat import chat_with_contract

# Page configuration
st.set_page_config(
    page_title="AI-Powered Contract Analyzer",
    page_icon="⚖️",
    layout="wide"
)

# Initialize session state
if 'contract_text' not in st.session_state:
    st.session_state.contract_text = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None

# Header
st.title("⚖️ AI-Powered Contract Analyzer")
st.markdown("This tool helps **Hari and Winston Associates LLC** review contracts by highlighting risks and suggesting improvements.")

# Create tabs
tab1, tab2 = st.tabs(["📊 Analysis Dashboard", "💬 Chat with Contract"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Contract Upload")
        st.markdown("Upload a contract document (.docx) to analyze its clauses, identify risks, and get mitigation suggestions.")
        
        uploaded_file = st.file_uploader("Choose a .docx file", type="docx")
        
        if uploaded_file is not None:
            try:
                contract_text = parse_document(uploaded_file)
                st.session_state.contract_text = contract_text
                st.success(f"✅ Document uploaded successfully! ({len(contract_text)} characters)")
            except Exception as e:
                st.error(f"Error parsing document: {str(e)}")
        
        if st.button("Analyze Contract", type="primary"):
            if st.session_state.contract_text:
                with st.spinner("Analyzing contract..."):
                    try:
                        # Perform analysis
                        analysis_result = analyze_contract(st.session_state.contract_text)
                        
                        # Debug: Print what we got
                        st.write("**Debug - Analysis Result:**")
                        st.json(analysis_result)
                        
                        if analysis_result and "error" not in analysis_result:
                            st.session_state.analysis_data = analysis_result
                            
                            # Create retriever for chatbot
                            try:
                                retriever = get_pinecone_retriever(
                                    st.session_state.contract_text, 
                                    analysis_result
                                )
                                if retriever:
                                    st.session_state.retriever = retriever
                                    st.success("✅ Analysis complete! Chat is ready.")
                                else:
                                    st.success("✅ Analysis complete! (Chat unavailable - vector store failed)")
                            except Exception as e:
                                st.success("✅ Analysis complete!")
                                st.warning(f"Chat setup failed: {str(e)}")
                        else:
                            error_msg = analysis_result.get("error", "Unknown error") if analysis_result else "Analysis failed"
                            st.error(f"❌ {error_msg}")
                            
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
            else:
                st.error("Please upload a contract first.")
    
    with col2:
        st.header("Analysis Results")
        
        if st.session_state.analysis_data:
            # Debug: Show raw data structure
            st.write("**Debug - Raw Analysis Data:**")
            st.json(st.session_state.analysis_data)
            
            # Handle different possible response structures
            analysis = st.session_state.analysis_data
            
            # Check if it's wrapped in "analysis" key
            if "analysis" in analysis:
                analysis = analysis["analysis"]
            
            # Contract Summary
            if "summary" in analysis:
                st.subheader("📄 Contract Summary")
                st.write(analysis["summary"])
            
            # Overall Risk Assessment
            if "overall_risk" in analysis:
                st.subheader("⚠️ Overall Risk Assessment")
                risk_level = analysis["overall_risk"]
                if risk_level.lower() == "high":
                    st.error(f"🚨 {risk_level} Risk")
                elif risk_level.lower() == "medium":
                    st.warning(f"⚠️ {risk_level} Risk")
                else:
                    st.success(f"✅ {risk_level} Risk")
            
            # Clause Analysis
            if "clauses" in analysis and analysis["clauses"]:
                st.subheader("📋 Detailed Clause Analysis")
                
                for i, clause in enumerate(analysis["clauses"]):
                    if isinstance(clause, dict):
                        with st.expander(f"Clause {i+1}: {clause.get('clause_type', 'Unknown')}"):
                            
                            # Risk Level Badge
                            risk = clause.get("risk_level", "Unknown")
                            if risk.lower() == "high":
                                st.error(f"🚨 Risk Level: {risk}")
                            elif risk.lower() == "medium":
                                st.warning(f"⚠️ Risk Level: {risk}")
                            else:
                                st.success(f"✅ Risk Level: {risk}")
                            
                            # Clause Text
                            if "text" in clause:
                                st.markdown("**Clause Text:**")
                                st.write(clause["text"])
                            
                            # Risk Analysis
                            if "risk_analysis" in clause:
                                st.markdown("**Risk Analysis:**")
                                st.write(clause["risk_analysis"])
                            
                            # Suggestion
                            if "suggestion" in clause:
                                st.markdown("**Suggested Improvement:**")
                                st.info(clause["suggestion"])
            else:
                st.info("No clause analysis available in the results.")
                
            # Show raw response if available for debugging
            if "raw_response" in st.session_state.analysis_data:
                with st.expander("🔍 Debug - Raw AI Response"):
                    st.text(st.session_state.analysis_data["raw_response"])
                    
        else:
            st.info("📄 Upload and analyze a contract to see results here.")

with tab2:
    st.header("💬 Chat with Contract")
    
    if not st.session_state.analysis_data:
        st.info("📄 Please analyze a contract first to enable chat functionality.")
    elif not st.session_state.retriever:
        st.warning("⚠️ Chat functionality is unavailable. The contract analysis completed but the chatbot setup failed.")
        st.info("You can still view the analysis results in the Analysis Dashboard tab.")
        
        # Show what went wrong
        if st.button("🔧 Debug Vector Store Issue"):
            st.write("**Attempting to debug vector store setup...**")
            try:
                from chatbot.vector_store import get_pinecone_retriever
                retriever = get_pinecone_retriever(st.session_state.contract_text, st.session_state.analysis_data)
                if retriever:
                    st.session_state.retriever = retriever
                    st.success("✅ Vector store fixed! Chat is now available.")
                    st.experimental_rerun()
                else:
                    st.error("❌ Vector store setup still failing.")
            except Exception as e:
                st.error(f"❌ Vector store error: {str(e)}")
    else:
        st.success("✅ Chat is ready! Ask questions about your contract.")
        
        user_question = st.text_input("Ask a question about the contract:", key="chat_input")
        
        if user_question:
            with st.spinner("Thinking..."):
                try:
                    response = chat_with_contract(user_question, st.session_state.retriever)
                    st.markdown("**Answer:**")
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Sample questions
        st.markdown("**💡 Sample Questions:**")
        sample_questions = [
            "What is the total contract value?",
            "Who owns the intellectual property?",
            "What are the termination conditions?",
            "What are the main risks in this contract?",
            "Summarize the payment terms."
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question[:20]}"):
                with st.spinner("Thinking..."):
                    try:
                        response = chat_with_contract(question, st.session_state.retriever)
                        st.markdown("**Answer:**")
                        st.write(response)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This AI-powered tool helps legal professionals:
    
    - 📊 **Analyze contracts** for risks and issues
    - ⚠️ **Identify problematic clauses**  
    - 💡 **Get improvement suggestions**
    - 💬 **Ask questions** about contract details
    
    Built for **Hari and Winston Associates LLC**
    """)
    
    if st.session_state.analysis_data:
        st.success("✅ Contract analyzed")
        if st.session_state.retriever:
            st.success("✅ Chat ready")
        else:
            st.warning("⚠️ Chat unavailable")
    else:
        st.info("📄 No contract analyzed yet")