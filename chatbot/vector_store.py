# chatbot/vector_store.py - FIXED VERSION
from pinecone import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
import config

def get_pinecone_retriever(contract_text: str, analysis_data: dict):
    """
    Creates a Pinecone retriever for the contract and analysis data.
    """
    if not analysis_data or not isinstance(analysis_data, dict):
        print("Warning: Invalid analysis data")
        return None

    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=config.PINECONE_API_KEY)
        index = pc.Index(config.PINECONE_INDEX_NAME)

        # Use local embeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Prepare documents
        documents = []
        metadatas = []

        # Add contract text
        documents.append(contract_text)
        metadatas.append({"type": "contract", "section": "full_contract"})

        # Handle different data structures - the analysis might be direct or wrapped
        analysis = analysis_data
        if "analysis" in analysis_data:
            analysis = analysis_data["analysis"]
        
        print(f"Debug: Analysis keys found: {list(analysis.keys())}")
        
        # Add summary if available
        if "summary" in analysis:
            documents.append(analysis["summary"])
            metadatas.append({"type": "summary", "section": "contract_summary"})
            print("Added summary to vector store")

        # Add clauses if available
        if "clauses" in analysis and analysis["clauses"]:
            for i, clause in enumerate(analysis["clauses"]):
                if isinstance(clause, dict):
                    if "text" in clause:
                        documents.append(clause["text"])
                        metadatas.append({
                            "type": "clause",
                            "section": f"clause_{i}",
                            "risk_level": clause.get("risk_level", "unknown"),
                            "clause_type": clause.get("clause_type", "unknown")
                        })
                    
                    if "risk_analysis" in clause:
                        documents.append(clause["risk_analysis"])
                        metadatas.append({
                            "type": "risk_analysis", 
                            "section": f"clause_{i}_risk"
                        })
                    
                    if "suggestion" in clause:
                        documents.append(clause["suggestion"])
                        metadatas.append({
                            "type": "suggestion",
                            "section": f"clause_{i}_suggestion"
                        })
            
            print(f"Added {len(analysis['clauses'])} clauses to vector store")
        else:
            print("Warning: No clauses found in analysis data")

        # Clear existing data
        try:
            index.delete(delete_all=True)
            print("Cleared existing vectors from index")
        except Exception as e:
            print(f"Warning: Could not clear index: {e}")

        # Create vector store
        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            text_key="text"
        )
        
        # Add documents
        if len(documents) > 1:  # More than just the contract text
            vector_store.add_texts(texts=documents, metadatas=metadatas)
            print(f"Successfully added {len(documents)} documents to Pinecone")
            
            # Return retriever
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            print("✅ Vector store retriever created successfully")
            return retriever
        else:
            print("Warning: Only contract text available, no analysis data to add")
            return None

    except Exception as e:
        print(f"Error creating retriever: {str(e)}")
        import traceback
        print(f"Full error trace: {traceback.format_exc()}")
        return None