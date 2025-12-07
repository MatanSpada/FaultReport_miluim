import os
from sheets_api import add_report_to_sheet
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.utils import secure_filename
from sheets_api import get_reports_by_apartment
from apartments import APARTMENTS


# -------------------------
# הגדרות בסיסיות
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "change_this_to_a_random_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB לקובץ

# -------------------------
# ראוטים
# -------------------------

@app.route("/")
def index():
    """דף בחירת דירה"""
    return render_template("index.html", apartments=APARTMENTS)


@app.route("/apartment/<apt_id>")
def apartment_dashboard(apt_id):
    """דשבורד לדירה ספציפית"""

    if apt_id not in APARTMENTS:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    apt_name = APARTMENTS[apt_id]
    reports = get_reports_by_apartment(apt_id)

    return render_template(
        "dashboard.html",
        apartment_id=apt_id,
        apartment_name=apt_name,
        reports=reports
    )



@app.route("/apartment/<apt_id>/report/new/step1", methods=["GET", "POST"])
def report_step1(apt_id):
    if apt_id not in APARTMENTS:
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
    if apt_id not in APARTMENTS:
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
    if apt_id not in APARTMENTS:
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

        # להכין תיאור מלא שמשלב פריט + תיאור חופשי
        item = draft.get("item", "")
        description = draft.get("description", "")
        full_description = description
        if item:
            if description:
                full_description = f"{item} - {description}"
            else:
                full_description = item

        # שמירת הדיווח בגוגל שיטס
        report_id = add_report_to_sheet(
            apartment_id=apt_id,
            room=draft["room"],
            issue_type=draft["issue_type"],
            description=full_description,
            priority=draft.get("priority", "normal"),
            image_url=""  # בשלב הזה בלי קישור לתמונה – נטפל בזה בהמשך
        )

        # לנקות את הדראפט
        session.pop("report_draft", None)

        flash(f"דיווח #{report_id} נשלח בהצלחה!", "success")
        return redirect(url_for("apartment_dashboard", apt_id=apt_id))

    return render_template("report_step3.html", apartment_id=apt_id, draft=draft)


@app.route("/apartment/<apt_id>/report/<int:report_id>/set_status", methods=["POST"])
def set_status(apt_id, report_id):
    new_status = request.form.get("status")

    if apt_id not in APARTMENTS:
        flash("דירה לא קיימת", "error")
        return redirect(url_for("index"))

    from sheets_api import update_report_status

    ok = update_report_status(report_id, new_status)

    if ok:
        flash("סטטוס עודכן!", "success")
    else:
        flash("שגיאה בעדכון הסטטוס", "error")

    return redirect(url_for("apartment_dashboard", apt_id=apt_id))



if __name__ == "__main__":
    # הרצה מקומית
    app.run(host="0.0.0.0", port=5000, debug=True)
