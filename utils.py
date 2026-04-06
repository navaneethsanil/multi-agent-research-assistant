import os

from langchain_mistralai import ChatMistralAI

from dotenv import load_dotenv
load_dotenv(override=True)



def initialize_llm():
    llm = ChatMistralAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        model=os.getenv("MODEL_NAME"),
        temperature=0,
        max_retries=2,
    )

    return llm