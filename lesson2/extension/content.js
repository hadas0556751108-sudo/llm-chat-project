// יצירת כפתור צף בדף האינטרנט
const btn = document.createElement("button");
btn.innerText = "📋 מילוי חכם מתז";
btn.style.position = "fixed";
btn.style.top = "10px";
btn.style.left = "10px";
btn.style.zIndex = "9999";
btn.style.padding = "10px 15px";
btn.style.backgroundColor = "#007bff";
btn.style.color = "white";
btn.style.border = "none";
btn.style.borderRadius = "5px";
btn.style.cursor = "pointer";
btn.style.fontWeight = "bold";
btn.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";

document.body.appendChild(btn);

// יצירת אלמנט לבחירת קובץ נסתר
const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.accept = "image/jpeg,image/png";
fileInput.style.display = "none";
document.body.appendChild(fileInput);

btn.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", async () => {
  if (!fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  btn.innerText = "⏳ מעבד תמונה...";
  btn.disabled = true;

  try {
    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(",")[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

    // פנייה לשרת ה-FastAPI הקיים
    const res = await fetch("http://127.0.0.1:8000/api/extract-id", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: base64, mime_type: file.type })
    });

    if (!res.ok) throw new Error("שגיאה בתקשורת מול השרת");

    const data = await res.json();

    // איתור שדות בטופס ומילוי אוטומטי
    const fieldMap = {
      id_number: ["id_number", "tz", "id", "identity"],
      first_name: ["first_name", "fname", "firstname", "name"],
      last_name: ["last_name", "lname", "lastname", "family"],
      birth_date: ["birth_date", "bdate", "dob", "birthdate"]
    };

    for (const [key, val] of Object.entries(data)) {
      if (!val) continue;
      const possibleIds = fieldMap[key] || [key];
      for (const id of possibleIds) {
        const el = document.getElementById(id) || document.querySelector(`input[name="${id}"]`);
        if (el) {
          el.value = val;
          break;
        }
      }
    }

    btn.innerText = "✅ הושלם בהצלחה!";
  } catch (err) {
    alert("שגיאה במילוי הטופס: " + err.message);
    btn.innerText = "📋 מילוי חכם מתז";
  } finally {
    btn.disabled = false;
  }
});