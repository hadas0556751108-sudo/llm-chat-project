from datetime import datetime
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import sys
if getattr(sys, 'frozen', False):
    env_path = Path(sys.executable).parent / ".env"
else:
    env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY חסר בקובץ ה-.env")

client = OpenAI(api_key=api_key)


# 1. הפונקציה המחזירה את התאריך הנוכחי כמחרוזת
def get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# 2. הגדרת ה-JSON SCHEMA עבור ה-Tool
get_date_tool = {
    "type": "function",
    "name": "get_date",
    "description": "Returns the current date in YYYY-MM-DD format.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "strict": True,
}

tools = [get_date_tool]
if __name__ == "__main__":
    # 3. קריאה ל-OpenAI Responses API עם ה-Tools
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="אתה עוזר סוכן שיודע מה התאריך היום באמצעות שימוש בכלים העומדים לרשותך.",
        input="מה התאריך היום?",
        tools=tools,
    )

    # 4. הדפסת התשובה המלאה בפורמט JSON לבדיקת קריאת ה-Function Call
    print(response.to_json())