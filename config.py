import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
API_VERSION = "2024-02-01"
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")