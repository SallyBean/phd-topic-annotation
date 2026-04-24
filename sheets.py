"""Google Sheets backend for annotation app."""
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TOPICS_SHEET      = "topics"
ANNOTATIONS_SHEET = "annotations"
# categories stored as pipe-separated string to support multi-label
ANNOTATION_COLS   = ["topic_id", "model", "rater", "categories", "timestamp", "session_id"]


@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    return get_client().open_by_key(st.secrets["sheets"]["spreadsheet_id"])


def load_topics() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet(TOPICS_SHEET)
    return pd.DataFrame(ws.get_all_records())


def load_annotations() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet(ANNOTATIONS_SHEET)
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=ANNOTATION_COLS)
    return pd.DataFrame(data)


def save_annotation(topic_id: int, model: str, rater: str,
                    categories: list[str], session_id: str):
    """Save multi-label annotation — categories stored as pipe-separated string."""
    ws = get_spreadsheet().worksheet(ANNOTATIONS_SHEET)
    row = [
        topic_id,
        model,
        rater,
        "|".join(sorted(categories)),
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        session_id,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def update_annotation(topic_id: int, model: str, rater: str,
                      categories: list[str], session_id: str):
    """Overwrite an existing annotation for this rater+topic, or append if new."""
    ws = get_spreadsheet().worksheet(ANNOTATIONS_SHEET)
    records = ws.get_all_records()
    for i, rec in enumerate(records):
        if (str(rec.get("topic_id")) == str(topic_id)
                and rec.get("model") == model
                and rec.get("rater") == rater):
            row_num = i + 2  # 1-indexed + header row
            ws.update(f"D{row_num}:F{row_num}", [[
                "|".join(sorted(categories)),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                session_id,
            ]])
            return
    save_annotation(topic_id, model, rater, categories, session_id)


def initialise_sheets(topics_df: pd.DataFrame):
    """One-time setup: create/clear sheets and upload topics."""
    ss = get_spreadsheet()
    for sheet_name in [TOPICS_SHEET, ANNOTATIONS_SHEET]:
        try:
            ss.worksheet(sheet_name).clear()
        except gspread.WorksheetNotFound:
            ss.add_worksheet(title=sheet_name, rows=5000, cols=15)

    ws_topics = ss.worksheet(TOPICS_SHEET)
    ws_topics.update([topics_df.columns.tolist()] + topics_df.values.tolist())

    ws_ann = ss.worksheet(ANNOTATIONS_SHEET)
    ws_ann.append_row(ANNOTATION_COLS)
