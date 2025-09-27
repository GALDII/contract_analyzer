# core/analyzer.py
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import config
from core.prompts import ANALYSIS_PROMPT_TEMPLATE

def analyze_contract(contract_text: str) -> dict:
    """
    Analyzes the contract text using an LLM and returns a structured JSON object.
    """
    
    # Try multiple configuration approaches
    llm_configs = [
        # Config 1: deployment_name parameter
        {
            "api_key": config.API_KEY,
            "api_version": config.API_VERSION,
            "azure_endpoint": config.AZURE_ENDPOINT,
            "deployment_name": config.DEPLOYMENT_NAME,
            "temperature": 0
        },
        # Config 2: model parameter instead of deployment_name
        {
            "api_key": config.API_KEY,
            "api_version": config.API_VERSION,
            "azure_endpoint": config.AZURE_ENDPOINT,
            "model": config.DEPLOYMENT_NAME,
            "temperature": 0
        },
        # Config 3: azure_deployment parameter
        {
            "api_key": config.API_KEY,
            "api_version": config.API_VERSION,
            "azure_endpoint": config.AZURE_ENDPOINT,
            "azure_deployment": config.DEPLOYMENT_NAME,
            "temperature": 0
        }
    ]
    
    last_error = None
    
    for i, llm_config in enumerate(llm_configs):
        try:
            print(f"Trying Azure OpenAI configuration {i+1}...")
            llm = AzureChatOpenAI(**llm_config)

            parser = JsonOutputParser()

            prompt = PromptTemplate(
                template=ANALYSIS_PROMPT_TEMPLATE,
                input_variables=["contract_text"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )

            chain = prompt | llm | parser
            analysis_result = chain.invoke({"contract_text": contract_text})
            
            print(f"✅ Success with configuration {i+1}")
            return analysis_result
            
        except Exception as e:
            print(f"❌ Configuration {i+1} failed: {str(e)}")
            last_error = e
            continue
    
    # If all configurations failed, try direct OpenAI approach
    try:
        print("Trying direct OpenAI client as fallback...")
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=config.API_KEY,
            api_version=config.API_VERSION,
            azure_endpoint=config.AZURE_ENDPOINT
        )
        
        # Create a simplified prompt for direct API call
        prompt_text = f"""
        Analyze this contract and return a JSON response with the following structure:
        {{
            "analysis": {{
                "summary": "Brief contract overview",
                "overall_risk": "High/Medium/Low",
                "clauses": [
                    {{
                        "clause_type": "Payment Terms",
                        "text": "Relevant clause text",
                        "risk_level": "High/Medium/Low",
                        "risk_analysis": "Risk explanation",
                        "suggestion": "Improvement suggestion"
                    }}
                ]
            }}
        }}
        
        Contract text:
        {contract_text[:3000]}...
        
        Return only valid JSON:
        """
        
        response = client.chat.completions.create(
            model=config.DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0,
            max_tokens=2000
        )
        
        # Try to parse the response as JSON
        import json
        response_text = response.choices[0].message.content
        
        # Clean up response text (remove markdown formatting if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        print("✅ Direct OpenAI client worked!")
        return result
        
    except Exception as direct_error:
        print(f"❌ Direct OpenAI also failed: {str(direct_error)}")
    
    return {"error": f"All connection attempts failed. Last error: {str(last_error)}"}