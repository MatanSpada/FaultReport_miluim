import os
import json
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.utils import secure_filename

# -------------------------
# הגדרות בסיסיות
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "change_this_to_a_random_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB לקובץ

# -------------------------
# פונקציות עזר לנתונים
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "last_report_id": 0,
            "apartments": {
                "1": {"name": "רותם", "reports": []},
                "2": {"name": "דפנה", "reports": []},
                "3": {"name": "ארז", "reports": []},
                "4": {"name": "אורן", "reports": []},
                "5": {"name": "מוריה", "reports": []},
                "6": {"name": "זקיף מוריה", "reports": []},
                "7": {"name": "אגוז", "reports": []},
                "8": {"name": "מלונית אגוז", "reports": []},
                "9": {"name": "ורד", "reports": []},
                "10": {"name": "מלונית ורד", "reports": []},
                "11": {"name": "אקליפטוס", "reports": []},
                "12": {"name": "זקיף אקליפטוס", "reports": []},
            }
        }
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_report_id(data):
    data["last_report_id"] += 1
    return data["last_report_id"]


# -------------------------
# ראוטים
# -------------------------

@app.route("/")
def index():
    """דף בחירת דירה"""
    data = load_data()
    apartments = data["apartments"]
    return render_template("index.html", apartments=apartments)


@app.route("/apartment/<apt_id>")
def apartment_dashboard(apt_id):
    """דשבורד לדירה ספציפית"""
    data = load_data()
    apartments = data["apartments"]

    if apt_id not in apartments:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    apt = apartments[apt_id]
    # למיין דיווחים מהחדש לישן
    reports = sorted(apt["reports"], key=lambda r: r["id"], reverse=True)

    return render_template("dashboard.html", apartment_id=apt_id, apartment=apt, reports=reports)


@app.route("/apartment/<apt_id>/report/new/step1", methods=["GET", "POST"])
def report_step1(apt_id):
    data = load_data()
    if apt_id not in data["apartments"]:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        room = request.form.get("room")
        issue_type = request.form.get("issue_type")

        if not room or not issue_type:
            flash("יש למלא את כל השדות", "error")
        else:
            # לשמור בדרפט בסשן
            session["report_draft"] = {
                "apartment_id": apt_id,
                "room": room,
                "issue_type": issue_type,
            }
            return redirect(url_for("report_step2", apt_id=apt_id))

    return render_template("report_step1.html", apartment_id=apt_id)


@app.route("/apartment/<apt_id>/report/new/step2", methods=["GET", "POST"])
def report_step2(apt_id):
    data = load_data()
    if apt_id not in data["apartments"]:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    draft = session.get("report_draft")
    if not draft or draft.get("apartment_id") != apt_id:
        flash("הדיווח לא הושלם, נא להתחיל מחדש.", "error")
        return redirect(url_for("report_step1", apt_id=apt_id))

    if request.method == "POST":
        item = request.form.get("item")
        description = request.form.get("description", "")
        priority = request.form.get("priority")

        if not item or not priority:
            flash("יש למלא את כל השדות החובה", "error")
        else:
            draft["item"] = item
            draft["description"] = description
            draft["priority"] = priority
            session["report_draft"] = draft
            return redirect(url_for("report_step3", apt_id=apt_id))

    return render_template("report_step2.html", apartment_id=apt_id, draft=draft)


@app.route("/apartment/<apt_id>/report/new/step3", methods=["GET", "POST"])
def report_step3(apt_id):
    data = load_data()
    if apt_id not in data["apartments"]:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    draft = session.get("report_draft")
    if not draft or draft.get("apartment_id") != apt_id:
        flash("הדיווח לא הושלם, נא להתחיל מחדש.", "error")
        return redirect(url_for("report_step1", apt_id=apt_id))

    if request.method == "POST":
        photo_file = request.files.get("photo")
        photo_filename = None

        if photo_file and photo_file.filename:
            safe_name = secure_filename(photo_file.filename)
            # להוסיף חותמת זמן כדי למנוע התנגשות שמות
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            name, ext = os.path.splitext(safe_name)
            final_name = f"{name}_{timestamp}{ext}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
            photo_file.save(save_path)
            photo_filename = final_name

        # יצירת הדיווח הסופי
        report_id = create_report_id(data)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = {
            "id": report_id,
            "created_at": now_str,
            "room": draft["room"],
            "issue_type": draft["issue_type"],   # broken / missing / other
            "item": draft.get("item", ""),
            "description": draft.get("description", ""),
            "priority": draft.get("priority", "normal"),
            "photo_filename": photo_filename,    # יכול להיות None
            "status": "received",               # התחלה: התקבל
        }

        data["apartments"][apt_id]["reports"].append(report)
        save_data(data)

        # לנקות את הדראפט
        session.pop("report_draft", None)

        flash(f"דיווח #{report_id} נשלח בהצלחה!", "success")
        return redirect(url_for("apartment_dashboard", apt_id=apt_id))

    return render_template("report_step3.html", apartment_id=apt_id, draft=draft)


# אופציונלי – עדכון סטטוס (כרגע רק דוגמה פשוטה)
@app.route("/apartment/<apt_id>/report/<int:report_id>/set_status", methods=["POST"])
def set_status(apt_id, report_id):
    new_status = request.form.get("status")
    data = load_data()

    if apt_id not in data["apartments"]:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    apt = data["apartments"][apt_id]
    found = False
    for r in apt["reports"]:
        if r["id"] == report_id:
            r["status"] = new_status
            found = True
            break

    if found:
        save_data(data)
        flash("סטטוס עודכן", "success")
    else:
        flash("דיווח לא נמצא", "error")

    return redirect(url_for("apartment_dashboard", apt_id=apt_id))


if __name__ == "__main__":
    # הרצה מקומית
    app.run(host="0.0.0.0", port=5000, debug=True)
