
import os
import ssl
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, DefaultHttpxClient

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL", "gpt-4o-mini")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

if not model:
    raise RuntimeError("MODEL is missing in .env")

ssl_ctx = ssl.create_default_context()
ssl_ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT

client = OpenAI(
    api_key=api_key,
    http_client=DefaultHttpxClient(verify=ssl_ctx)
)

if __name__ == "__main__":
    response = client.responses.create(
        model=model,
        input="שלום"
    )
    print(response.output_text)
