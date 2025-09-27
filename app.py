import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
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

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-left: 20px;
        padding-right: 20px;
        color: #262730 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #1f77b4;
        color: #262730 !important;
    }
    
    .upload-section {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: rgba(31, 119, 180, 0.1);
        margin: 1rem 0;
    }
    
    .upload-section h3 {
        color: #1f77b4 !important;
        margin-bottom: 1rem;
    }
    
    .upload-section p {
        color: #666 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'contract_text' not in st.session_state:
    st.session_state.contract_text = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'contract_score' not in st.session_state:
    st.session_state.contract_score = None

def calculate_contract_score(analysis_data):
    """Calculate overall contract score based on analysis"""
    if not analysis_data:
        return 0
    
    analysis = analysis_data
    if "analysis" in analysis_data:
        analysis = analysis_data["analysis"]
    
    # Base score
    score = 100
    
    # Get clause data
    clauses = analysis.get("clauses", [])
    if not clauses:
        return 50  # Neutral score if no clauses
    
    # Calculate risk deductions
    high_risk_count = sum(1 for clause in clauses if isinstance(clause, dict) and clause.get("risk_level", "").lower() == "high")
    medium_risk_count = sum(1 for clause in clauses if isinstance(clause, dict) and clause.get("risk_level", "").lower() == "medium")
    low_risk_count = sum(1 for clause in clauses if isinstance(clause, dict) and clause.get("risk_level", "").lower() == "low")
    
    total_clauses = len(clauses)
    
    # Deduct points based on risk distribution
    if total_clauses > 0:
        high_risk_penalty = (high_risk_count / total_clauses) * 40  # Max 40 points deduction
        medium_risk_penalty = (medium_risk_count / total_clauses) * 20  # Max 20 points deduction
        
        score = max(10, score - high_risk_penalty - medium_risk_penalty)
    
    return round(score, 1)

def create_risk_distribution_chart(analysis_data):
    """Create risk distribution pie chart"""
    analysis = analysis_data
    if "analysis" in analysis_data:
        analysis = analysis_data["analysis"]
    
    clauses = analysis.get("clauses", [])
    
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    
    for clause in clauses:
        if isinstance(clause, dict):
            risk_level = clause.get("risk_level", "Unknown").title()
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
    
    # Only create chart if there are clauses
    if sum(risk_counts.values()) == 0:
        return None
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(risk_counts.keys()),
        values=list(risk_counts.values()),
        hole=.3,
        marker_colors=['#ff6b6b', '#ffa726', '#66bb6a']
    )])
    
    fig.update_layout(
        title="Risk Distribution by Clause",
        showlegend=True,
        height=400,
        font=dict(size=14)
    )
    
    return fig

def display_score_card(score):
    """Display score with color coding"""
    if score >= 80:
        color = "#4caf50"  # Green
        status = "Excellent"
        icon = "🟢"
    elif score >= 60:
        color = "#ff9800"  # Orange
        status = "Good"
        icon = "🟡"
    elif score >= 40:
        color = "#ff5722"  # Red-Orange
        status = "Needs Attention"
        icon = "🟠"
    else:
        color = "#f44336"  # Red
        status = "High Risk"
        icon = "🔴"
    
    # Use Streamlit's built-in metric instead of custom HTML
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(
            label="Contract Score", 
            value=f"{score}/100",
            delta=f"{status}"
        )
        
        # Add a simple colored indicator using Streamlit's built-in colors
        if score >= 80:
            st.success(f"{icon} {status} - Score: {score}")
        elif score >= 60:
            st.warning(f"{icon} {status} - Score: {score}")
        else:
            st.error(f"{icon} {status} - Score: {score}")

# Header with company branding
st.title("⚖️ AI-Powered Contract Analyzer")
st.markdown("**Hari and Winston Associates LLC** - This tool helps review contracts by highlighting risks and suggesting improvements.")

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
                            
                            # Calculate score
                            score = calculate_contract_score(analysis_result)
                            st.session_state.contract_score = score
                            
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
            # Show contract score if available
            if st.session_state.contract_score:
                display_score_card(st.session_state.contract_score)
                
                # Create analytics section
                st.markdown("### 📈 Quick Analytics")
                
                analysis = st.session_state.analysis_data
                if "analysis" in analysis:
                    analysis = analysis["analysis"]
                
                clauses = analysis.get("clauses", [])
                
                if clauses:
                    # Calculate metrics
                    total_clauses = len(clauses)
                    high_risk = sum(1 for c in clauses if isinstance(c, dict) and c.get("risk_level", "").lower() == "high")
                    medium_risk = sum(1 for c in clauses if isinstance(c, dict) and c.get("risk_level", "").lower() == "medium")
                    low_risk = sum(1 for c in clauses if isinstance(c, dict) and c.get("risk_level", "").lower() == "low")
                    
                    # Display metrics in columns
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("Total Clauses", total_clauses)
                    with col_b:
                        st.metric("High Risk", high_risk, delta=-high_risk if high_risk > 0 else None)
                    with col_c:
                        st.metric("Medium Risk", medium_risk, delta=-medium_risk if medium_risk > 0 else None)
                    with col_d:
                        st.metric("Low Risk", low_risk, delta=low_risk if low_risk > 0 else None)
                    
                    # Risk distribution chart
                    risk_fig = create_risk_distribution_chart(st.session_state.analysis_data)
                    if risk_fig:
                        st.plotly_chart(risk_fig, use_container_width=True)
            
            # Debug: Show raw data structure
            with st.expander("🔍 Debug - Raw Analysis Data"):
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
                    st.rerun()
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
                    st.info(response)
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
                        st.info(response)
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
    
    # Status indicators
    st.markdown("### 📊 System Status")
    
    if st.session_state.contract_text:
        st.success("✅ Document uploaded")
    else:
        st.info("📄 No document uploaded")
    
    if st.session_state.analysis_data:
        st.success("✅ Contract analyzed")
        if st.session_state.contract_score:
            st.metric("Contract Score", f"{st.session_state.contract_score}/100")
        if st.session_state.retriever:
            st.success("✅ Chat ready")
        else:
            st.warning("⚠️ Chat unavailable")
    else:
        st.info("📄 No contract analyzed yet")