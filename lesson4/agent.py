from nodes import (
    classifier,
    draft_creator,
    draft_evaluator,
    hitl,
    send_response,
    end_irrelevant,
)
PASS_THRESHOLD = 0.85   # ציון מינימלי כדי להעביר למגייסת
MAX_RETRIES = 3         # מקסימום ניסיונות כתיבה בכל סבב


def run_agent(message: str) -> dict:
    # ---------- סטייט: מקום אחד שמחזיק את כל המידע ----------
    state = {
        "message": message,
        "category": "",
        "confidence": 0.0,
        "draft": "",
        "score": 0.0,
        "feedback": "",
        "retries": 0,
        "approved": False,
    }

    # ---------- צומת 1: סיווג ----------
    c = classifier(state["message"])
    state["category"] = c.category
    state["confidence"] = c.confidence
    print(f"[classifier] {c.category} ({c.confidence})")

    # ---------- פיצול: פנייה לא רלוונטית מסתיימת כאן ----------
    if state["category"] == "irrelevant":
        return end_irrelevant(state["category"])

    # ---------- לולאה חיצונית: חוזרת רק אם המגייסת דחתה ----------
    while not state["approved"]:
        state["retries"] = 0  # כל סבב חדש מתחיל ספירה מחדש

        # ---------- לולאה פנימית: יוצר <-> מעריך ----------
        while state["retries"] < MAX_RETRIES:
            # צומת 2: יצירת טיוטה (עם משוב אם יש)
            d = draft_creator(
                state["message"],
                state["category"],
                state["confidence"],
                previous_draft=state["draft"],
                feedback=state["feedback"],
            )
            state["draft"] = d.draft
            state["retries"] += 1
            print(f"[draft_creator] ניסיון {state['retries']}")

            # צומת 3: הערכת איכות
            e = draft_evaluator(state["message"], state["category"], state["draft"])
            state["score"] = e.score
            state["feedback"] = e.feedback
            print(f"[draft_evaluator] ציון {e.score}")

            # ניתוב: ציון טוב, יוצאים מהלולאה הפנימית
            if state["score"] >= PASS_THRESHOLD:
                break

        # ---------- צומת 4: אישור אנושי ----------
        h = hitl(
            state["message"],
            state["category"],
            state["draft"],
            state["score"],
            state["feedback"],
        )

        if h.action == "reject":
            # דחייה: ההערות האנושיות הופכות למשוב, והלולאה החיצונית חוזרת
            state["feedback"] = h.feedback
            state["approved"] = False
        else:
            # אישור או עריכה: הנוסח הסופי הוא של האדם
            state["draft"] = h.draft
            state["approved"] = True

    # ---------- צומת 5: שליחה ----------
    return send_response(state["message"], state["category"], state["draft"])


if __name__ == "__main__":
    # דוגמה 1: שאלה על משרה
    message = (
        "שלום, רציתי לשאול לגבי משרת מפתח/ת תוכנה אצלכם — "
        "האם העבודה היא היברידית וכמה ימים מגיעים למשרד?"
    )
    # דוגמה 2: הגשת מועמדות
    # message = "היי, שמי נועה, בוגרת הנדסת תוכנה, מצרפת פרטים להגשת מועמדות למשרת ג'וניור."
    # דוגמה 3: פנייה לא רלוונטית
    # message = "מבצע מטורף! קנו חבילת פרסום לעסק שלכם ב-50% הנחה!"

    result = run_agent(message)
    print(result)