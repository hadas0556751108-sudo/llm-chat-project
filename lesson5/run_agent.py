from nodes import (
    classify_comment,
    rewrite_comment,
    human_review,
    reject_comment,
    notify_user,
    save_and_publish,
)

CONFIDENCE_THRESHOLD = 0.7
MAX_RETRIES = 2


def run_agent(post_subject: str,
              new_post: str,
              userId: int) -> dict:

    # ---------- שלב 1: בניית state ----------

    state = {
        "post_subject": post_subject,
        "new_post": new_post,
        "userId": userId,
        "category": "",
        "confidence": 0.0,
        "rewritten_new_post": "",
        "user_message": "",
        "approve": False
    }

    try:

        # ---------- שלב 2: סיווג ----------

        for attempt in range(MAX_RETRIES):
            try:
                state.update(classify_comment(state))
                break
            except Exception:
                if attempt == MAX_RETRIES - 1:
                    raise

        # ---------- שלב 3: ניתוב ----------
       
        if state["confidence"] < CONFIDENCE_THRESHOLD:

            state.update(human_review(state))
            state.update(reject_comment(state))

        # ---------- תגובה רלוונטית ----------

        elif state["category"] == "relevant":

            state["rewritten_new_post"] = state["new_post"]
            state["approve"] = True

            state.update(save_and_publish(state))

            state["user_message"] = "התגובה פורסמה בהצלחה"

        # ---------- פרטים אישיים ----------

        elif state["category"] == "personal_info":

            for attempt in range(MAX_RETRIES):
                try:
                    state.update(rewrite_comment(state))
                    break
                except Exception:
                    if attempt == MAX_RETRIES - 1:
                        raise

            if not state["rewritten_new_post"].strip():

                state.update(human_review(state))
                state.update(reject_comment(state))

            else:

                state["approve"] = True

                state.update(save_and_publish(state))
                state.update(notify_user(state))

        # ---------- בעייתית / לא קשורה ----------

        else:

            state.update(human_review(state))
            state.update(reject_comment(state))

    # ---------- טיפול בכשלים ----------

    except Exception:

        state["approve"] = False

        state.update(human_review(state))
        state.update(reject_comment(state))

    # אין לשמור את התגובה המקורית עם פרטים אישיים
    state["new_post"] = ""

    return state


if __name__ == "__main__":

    post_subject = "איך מקטינים עלויות טוקנים?"

    new_post = "אפשר להשתמש ב-prompt caching"
   
    result = run_agent(post_subject, new_post, 1)

    print(result)


    # Test cases:

# new_post = "אפשר להשתמש ב-prompt caching"
# בודק תגובה רלוונטית ופרסום אוטומטי.

# new_post = "מומלץ לקצר את הפרומפט. המייל שלי הוא test@example.com"
# בודק הסרת פרטים אישיים, פרסום ושליחת הודעה.

# new_post = "יש מבצע על רהיטים לבית בחצי מחיר"
# בודק תגובה לא קשורה, בדיקה אנושית ודחייה.

# new_post = "אין לכם מושג בתכנות"
# בודק תגובה בעייתית, דחייה והחלטה על חסימה (y/n).

# new_post = "אולי אפשר לעשות את זה בדרך אחרת, לא בטוח"
# מיועד לבדיקת ביטחון נמוך ומעבר לבדיקה אנושית.
# לא מובטח שהמודל יחזיר confidence נמוך מ-0.7.