import json
import os
from pathlib import Path
import ssl
import subprocess
import sys

from dotenv import load_dotenv
from openai import OpenAI, DefaultHttpxClient

# ייבוא הכלי הקיים מהקובץ main.py שכבר יצרת
from main import get_date, get_date_tool
if getattr(sys, 'frozen', False):
    env_path = Path(sys.executable).parent / ".env"
else:
    env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY חסר בקובץ ה-.env")

# התאמת SSL לעבודה תקינה מאחורי סינון רשת מקומי
ssl_ctx = ssl.create_default_context()
ssl_ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT

client = OpenAI(api_key=api_key, http_client=DefaultHttpxClient(verify=ssl_ctx))

# הגדרות מודל והגבלות (טוקנים וצעדים)
MODEL = "gpt-5.4-mini"
MAX_STEPS = 5            # מונע לולאה אינסופית של קריאות לכלים
MAX_OUTPUT_TOKENS = 1000 # מאוזן: מאפשר תשובות וקוד מלאים בלי לבזבז טוקנים


# כלי להרצת קוד פייתון
def exec_code(code: str) -> str:
    """מריצה קוד פייתון כתת-תהליך ומחזירה את הפלט (stdout + stderr)."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout + result.stderr


exec_code_tool = {
    "type": "function",
    "name": "exec_code",
    "description": "Runs the given Python code in a subprocess and returns its output (stdout and stderr). Use print() to see results.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to run.",
            }
        },
        "required": ["code"],
        "additionalProperties": False,
    },
    "strict": True,
}

# מיפוי כל הכלים הזמינים לסוכן
TOOLS_REGISTRY = {
    "get_date": get_date,
    "exec_code": exec_code,
}

tools = [get_date_tool, exec_code_tool]

SYSTEM_PROMPT = """
אתה סוכן עוזר למתכנתים.
עומדים לרשותך הכלים get_date (לקבלת התאריך הנוכחי) ו-exec_code (להרצת קוד פייתון).
כאשר מתבקשת פעולה חישובית או בדיקה בפייתון, השתמש ב-exec_code והקפד להשתמש ב-print() כדי להציג תוצאות.
כללי בטיחות מחייבים:
1. לעולם אל תקרא קבצי .env, מפתחות API או קבצים מחוץ לתיקיית העבודה הנוכחית.
2. אל תריץ קוד שמוחק קבצים, משנה הגדרות מערכת או פותח חיבורים חיצוניים.
3. אם הפלט ריק או שיש שגיאה, דווח על כך בכנות ואל תמציא תוצאות.
"""

inputs_list = [{"role": "system", "content": SYSTEM_PROMPT}]

print(">>> Assistant: שלום! אני כאן כדי לעזור לך. (ליציאה הקישי q)")

while True:
    user_input = input("\n>>> User: ")
    if user_input.strip().lower() == "q":
        break

    inputs_list.append({"role": "user", "content": user_input})
    steps = 0

    # לולאת האייג'נט הפנימית (עם הגבלת צעדים)
    while steps < MAX_STEPS:
        steps += 1

        response = client.responses.create(
            model=MODEL,
            input=inputs_list,
            tools=tools,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            reasoning={
                "effort": "low",
                "summary": "detailed",
            },
        )

        inputs_list += response.output

        # סינון והדפסת מחשבות (Reasoning)
        reasoning_items = [item for item in response.output if item.type == "reasoning"]
        for r in reasoning_items:
            for line in r.summary:
                print(">>> Assistant Thinks:", line.text)

        # סינון בקשות להפעלת כלים
        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            break

        for fc in function_calls:
            print(f">>> Tool Use: {fc.name}")
            try:
                args = json.loads(fc.arguments)

                # הגנת HITL מחמירה להרצת קוד
                if fc.name == "exec_code":
                    print("\n--- בקשת אישור להרצת קוד ---")
                    print(args.get("code", ""))
                    print("------------------------------")
                    is_approved = input(">>> האם לאשר הרצה? (הקישי y לאישור, כל מקש אחר לביטול): ")

                    if is_approved.strip().lower() != "y":
                        print(">>> ההרצה בוטלה על ידי המשתמש.")
                        inputs_list.append({
                            "type": "function_call_output",
                            "call_id": fc.call_id,
                            "output": "Tool Call - Not Approved by user.",
                        })
                        continue

                result = TOOLS_REGISTRY[fc.name](**args)

            except Exception as e:
                result = f"Error: {e}"

            trimmed_result = result[:2000]
            print(">>> Tool Result:", trimmed_result[:200])

            inputs_list.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": trimmed_result,
            })

    if steps >= MAX_STEPS:
        print(">>> Assistant: הגעתי למגבלת הצעדים המותרת לפעולה אחת.")
    elif response.output_text:
        print(">>> Assistant:", response.output_text)