# chatbot/chat.py
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import config

def chat_with_contract(question: str, retriever):
    """
    Processes a user question about the contract using the retriever and LLM.
    
    Args:
        question (str): The user's question
        retriever: The Pinecone retriever containing contract information
        
    Returns:
        str: The AI's response to the question
    """
    try:
        # Initialize the LLM
        llm = AzureChatOpenAI(
            temperature=0.3,
            api_version=config.API_VERSION,
            api_key=config.API_KEY,
            azure_endpoint=config.AZURE_ENDPOINT,
            deployment_name=config.DEPLOYMENT_NAME
        )

        # Create a custom prompt template for contract Q&A
        prompt_template = """
        You are a legal assistant helping to answer questions about a contract for Hari and Winston Associates LLC.
        
        Use the following contract information to answer the user's question accurately and concisely.
        If you don't find relevant information in the context, say so clearly.
        
        Context from contract:
        {context}
        
        Question: {question}
        
        Answer: Provide a clear, specific answer based on the contract information. If discussing risks or legal implications, be balanced and professional.
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        # Create the RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=False
        )

        # Get the response
        response = qa_chain.run(question)
        return response

    except Exception as e:
        return f"I apologize, but I encountered an error while processing your question: {str(e)}"