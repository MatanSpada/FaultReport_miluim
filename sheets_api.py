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
        image_url
    ]

    service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]}
    ).execute()

    return report_id


