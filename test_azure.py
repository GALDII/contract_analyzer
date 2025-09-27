#!/usr/bin/env python3
# test_azure.py - Quick Azure OpenAI Test

import config

def test_azure_openai():
    print("=== Azure OpenAI Test ===")
    print(f"Endpoint: {config.AZURE_ENDPOINT}")
    print(f"Deployment: {config.DEPLOYMENT_NAME}")
    print(f"API Version: {config.API_VERSION}")
    print(f"API Key: {config.API_KEY[:10]}...")
    print()

    try:
        from openai import AzureOpenAI
        
        # Test direct connection
        client = AzureOpenAI(
            api_key=config.API_KEY,
            api_version=config.API_VERSION,
            azure_endpoint=config.AZURE_ENDPOINT
        )
        
        print("Testing direct OpenAI connection...")
        response = client.chat.completions.create(
            model=config.DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
            max_tokens=5
        )
        
        print(f"✅ Direct OpenAI works: {response.choices[0].message.content}")
        
        # Test LangChain
        print("Testing LangChain connection...")
        from langchain_openai import AzureChatOpenAI
        
        llm = AzureChatOpenAI(
            api_key=config.API_KEY,
            api_version=config.API_VERSION,
            azure_endpoint=config.AZURE_ENDPOINT,
            deployment_name=config.DEPLOYMENT_NAME,
            temperature=0
        )
        
        response = llm.invoke("Hello, respond with just 'OK'")
        print(f"✅ LangChain works: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
        # Try alternative configurations
        print("\nTrying alternative configurations...")
        
        try:
            # Try with model parameter instead of deployment_name
            llm2 = AzureChatOpenAI(
                api_key=config.API_KEY,
                api_version=config.API_VERSION,
                azure_endpoint=config.AZURE_ENDPOINT,
                model=config.DEPLOYMENT_NAME,  # Try model instead
                temperature=0
            )
            
            response2 = llm2.invoke("Hello")
            print(f"✅ Alternative LangChain config works: {response2.content}")
            return "use_model_param"
            
        except Exception as e2:
            print(f"❌ Alternative also failed: {str(e2)}")
            
        return False

if __name__ == "__main__":
    result = test_azure_openai()
    print(f"\nTest result: {result}")