import pandas as pd


class DataCleaner:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()

    def _clean_data(self) -> None:
        self.df = self.df.dropna(subset=["Date", "Mine", "Production"])
        self.df = self.df[self.df["Date"] != "#N/A"]

    def _format_data(self) -> None:
        self.df["Date"] = pd.to_datetime(self.df["Date"])
        self.df["Production"] = pd.to_numeric(self.df["Production"], errors="coerce")

        total_prod = self.df.groupby("Date", as_index=False)["Production"].sum()
        total_prod["Mine"] = "Total"

        self.df = pd.concat([self.df, total_prod], ignore_index=True).sort_values(
            ["Date", "Mine"]
        )

    def get_clean_df(self) -> pd.DataFrame:
        self._clean_data()
        self._format_data()
        return self.df
