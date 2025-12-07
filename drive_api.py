from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# קובץ הקרדנצ'יאלס של ה-service account
CREDENTIALS_FILE = "google_api/credentials.json"

# ה-Drive Folder ID שלך
DRIVE_FOLDER_ID = "1_WDBBeudQy-QbdobtLkHLAO1NmG828Xn"


def get_drive_service():
    """
    יוצר חיבור מאובטח ל-Google Drive API.
    """
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=credentials)
    return service


def upload_image_to_drive(local_path, filename):
    """
    מעלה תמונה לתיקיית Apartments_Report_Images ומחזיר קישור ציבורי לצפייה.
    """
    service = get_drive_service()

    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID]
    }

    media = MediaFileUpload(local_path, mimetype="image/jpeg")

    # יוצרים את הקובץ בדרייב
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True
    ).execute()

    file_id = uploaded.get("id")

    # הופכים את הקובץ לנגיש לצפייה ציבורית
    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    # מחזירים URL תקין
    public_url = f"https://drive.google.com/uc?id={file_id}"

    return public_url

