from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

# ה-ID של ה-Google Sheets שלך
SPREADSHEET_ID = "1KMM7ynsIc0LR3c1G30ulxYh-AFo-dfetfNGwDYuvce8"

# טווח הגיליון (שם הטאב)
SHEET_NAME = "ApartmentReports"

# קובץ ה-credentials.json
CREDENTIALS_FILE = "google_api/credentials.json"

def get_sheet_service():
    """
    יוצר חיבור מאובטח ל-Google Sheets דרך service account.
    מחזיר אובייקט service שמאפשר לבצע פעולות קריאה/כתיבה.
    """
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()

def get_next_report_id():
    """
    קורא את כל הדיווחים מהגיליון ומחזיר report_id חדש רץ אוטומטית.
    אם אין אף דיווח — יוחזר 1.
    """
    service = get_sheet_service()

    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2:A"
    ).execute()

    rows = result.get("values", [])

    if not rows:
        return 1  # אין דיווחים עדיין

    last_id = int(rows[-1][0])  # A column = report_id
    return last_id + 1


def add_report_to_sheet(apartment_id, room, issue_type, description, priority, image_url=""):
    """
    מוסיף דיווח חדש לגיליון ApartmentReports.
    """
    service = get_sheet_service()

    report_id = get_next_report_id()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_row = [
        report_id,
        apartment_id,
        timestamp,
        room,
        issue_type,
        description,
        priority,
        "received"   # status
    ]

    service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]}
    ).execute()

    return report_id


def get_reports_by_apartment(apartment_id):
    """
    מחזיר את כל הדיווחים עבור דירה מסוימת מתוך Google Sheets.
    """
    service = get_sheet_service()

    # קוראים 8 עמודות בלבד: A → H
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2:H"
    ).execute()

    rows = result.get("values", [])

    reports = []
    for row in rows:

        # מבטיחים שכל שורה תהיה לפחות 8 תאים
        while len(row) < 8:
            row.append("")

        report_id, apt_id, created_at, room, issue_type, description, priority, status = row

        if str(apt_id) == str(apartment_id):
            reports.append({
                "id": int(report_id),
                "created_at": created_at,
                "room": room,
                "issue_type": issue_type,
                "description": description,
                "priority": priority,
                "status": status,     # כאן מושך משיטס באמת

                # כדי שהדשבורד לא יקרוס, נשים תמונה ריקה
                "photo_filename": None
            })

    # ממיינים מהחדש לישן
    reports.sort(key=lambda r: r["id"], reverse=True)

    return reports




def update_report_status(report_id, new_status):
    """
    מעדכן את הסטטוס של דיווח קיים בגוגל שיטס.
    """
    service = get_sheet_service()

    # קריאה של כל הדיווחים
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2:H"
    ).execute()

    rows = result.get("values", [])

    # צריך למצוא את השורה (מספר שורה) של הדיווח
    row_index = None
    for i, row in enumerate(rows, start=2):  # A2 היא שורה 2
        if str(row[0]) == str(report_id):    # report_id נמצא בעמודה A
            row_index = i
            break

    if row_index is None:
        return False

    # כותבים את הסטטוס החדש בעמודה H
    service.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!H{row_index}",
        valueInputOption="RAW",
        body={"values": [[new_status]]}
    ).execute()

    return True
