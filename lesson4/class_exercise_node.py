import os
from dotenv import load_dotenv
from fastapi import FastAPI, Path
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal
load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY חסר בקובץ ה-.env")

client = OpenAI(api_key=api_key)
app = FastAPI(title="Smart ID Form Extractor")

# --- הנחיות מערכת (System Prompts) ---

CLASIFIER_SYSTEM_PROMPT = """
אתה מסווג פניות. תפקידך לסווג הודעה שנשלחה בטופס צור קשר של אתר
לאחת משלוש קטגוריות בלבד:
- sales: פנייה הקשורה לרכישה, הצעת מחיר, התעניינות במוצרים או שירותים.
- support: פנייה הקשורה לתמיכה טכנית, תקלה, בעיה במוצר שנרכש או שאלת שירות.
- spam: הודעת זבל, פרסומת לא רלוונטית, ג'יבריש או פנייה ריקה.
"""

SALES_PROMPT = """
אתה נציג מכירות אדיב ומקצועי.
תפקידך לנסח טיוטת תשובה מזמינה, ברורה ומשכנעת לפניית לקוח מתעניין,
להציע פתרונות רלוונטיים ולהניע לפעולה (כגון שיחת ייעוץ או השלמת רכישה).
"""

SUPPORT_PROMPT = """
אתה נציג תמיכה טכנית סבלני ומקצועי.
תפקידך לנסח טיוטת תשובה ברורה, אמפתית ומדויקת לפתרון הבעיה שהלקוח תיאר,
כולל צעדים ברורים לפתרון במידת הצורך.
"""

PROMPTS_BY_CATEGORY = {
    "sales": SALES_PROMPT,
    "support": SUPPORT_PROMPT,
}

# --- מחלקות פלט מובנה ---

class ClassifierOutput(BaseModel):
    category: Literal["spam", "sales", "support"]
    confidence: float = Field(ge=0, le=1)

# --- פונקציות (Nodes) ---

def classifier(message: str) -> ClassifierOutput:
    response = client.responses.parse(
        model=model,
        instructions=CLASIFIER_SYSTEM_PROMPT,
        input=f"ההודעה מטופס צור קשר: {message}",
        text_format=ClassifierOutput
    )
    return response.output_parsed


def draft_creator(
    message: str,
    category: Literal["spam", "sales", "support"],
    confidence: float,
    feedback: str | None = None
) -> str:
    # בחירת הנחיות המערכת המתאימות לקטגוריה
    system_prompt = PROMPTS_BY_CATEGORY.get(category)
    if not system_prompt:
        return ""

    # הרכבת הקלט למודל
    user_input = f"הודעת הלקוח: {message}\nרמת ביטחון בסיווג: {confidence}"
    if feedback:
        user_input += f"\n\nהטיוטה הקודמת נדחתה. יש לשפר אותה לפי המשוב הבא:\n{feedback}"

    # קריאה ל-LLM ליצירת טיוטת התשובה
    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=user_input,
    )
    return response.output_text


def draft_evaluator():
    pass


def hitl():
    pass


def send_response():
    pass


# --- הרצה ובדיקה ---
if __name__ == "__main__":
    messages = [
        "שלום אני מתעניינת לגבי מחשב DELL חזק עד 3000 ש''ח",
        "",
        "למה המקלדת שקניתי לא מתחברת למחשב?"
    ]

    for msg in messages:
        print("=" * 40)
        print(f"הודעה: {msg}")
        
        # שלב 1: סיווג ההודעה
        classification = classifier(msg)
        print(f"סיווג: {classification.category} (ביטחון: {classification.confidence})")

        # שלב 2: יצירת טיוטה (רק אם לא ספאם)
        if classification.category != "spam":
            draft = draft_creator(
                message=msg,
                category=classification.category,
                confidence=classification.confidence
            )
            print(f"\nטיוטת תשובה:\n{draft}")
        else:
            print("ספאם - התהליך הסתיים.")