from dotenv import load_dotenv
from config import FIELDS, DANGEROUS_PREFIXES
import os
import pandas as pd
from fastapi import UploadFile
load_dotenv()

MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE_MB"))
MAX_ROWS = int(os.environ.get("MAX_ROWS"))

def sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].apply(
            lambda x: "'" + x if x.startswith(DANGEROUS_PREFIXES) else x
        )
    return df

def validate_dataset(content: str):
    if len(content) > MAX_FILE_SIZE :
        return False, f"File size exceeds the maximum limit of {MAX_FILE_SIZE} MB."

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return False, "File encoding is not UTF-8."
    
    try:
        df = pd.read_csv(
            pd.compat.StringIO(text),
            dtype=str,
            engine="python",
            sep=',',
            on_bad_lines="error"
            )
    except Exception as e:
        return False, "Invalid CSV format"

    if len(df) > MAX_ROWS:
        return False, f"Number of rows exceeds the maximum limit of {MAX_ROWS}."
    
    if not all(field in df.columns for field in FIELDS.values()):
        missing_fields = [field for field in FIELDS.values() if field not in df.columns]
        return False, f"Missing required fields: {', '.join(missing_fields)}."
    
    df = df[list(FIELDS.values())]

    df = sanitize_df(df)

    df.to_csv("sanitized_dataset.csv", index=False)

    return True, "Dataset is valid."