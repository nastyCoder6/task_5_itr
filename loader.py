import os

import gspread
import pandas as pd
from dotenv import load_dotenv


class DataLoader:
    def __init__(self) -> None:
        load_dotenv()
        self.url = "https://docs.google.com/spreadsheets/d/1UW5ApvxYBATsyiG6ZE1PCSpNNe7VZzy4ZzjTB8U_aBc/edit?gid=0#gid=0"
        self.apiKey = os.getenv("GOOGLE_CREDENTIALS")

    def load_data(self) -> pd.DataFrame:
        gc = gspread.api_key(self.apiKey)
        sh = gc.open_by_url(self.url)
        worksheet = sh.worksheet("DATA")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
