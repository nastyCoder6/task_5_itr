from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats


class DataAnalyzer:
    def __init__(self, data: pd.DataFrame) -> None:
        self.df = data

    def _get_metric(
        self, metric: Literal["mean", "median", "std"], mine_name: str = "Total"
    ) -> float:
        subset = self.df[self.df["Mine"] == mine_name]["Production"]
        return round(getattr(subset, metric)(), 2)

    def _get_iqr(self, mine_name: str = "Total") -> float:
        subset = self.df[self.df["Mine"] == mine_name]["Production"]
        q25, q75 = subset.quantile([0.25, 0.75])
        return round(q75 - q25, 2)

    def get_summary_table(self) -> pd.DataFrame:
        records = []
        mines = [m for m in self.df["Mine"].unique() if m != "Total"] + ["Total"]

        for mine in mines:
            records.append(
                {
                    "Mine": mine,
                    "Mean Daily Output": self._get_metric("mean", mine),
                    "Std Deviation": self._get_metric("std", mine),
                    "Median": self._get_metric("median", mine),
                    "IQR": self._get_iqr(mine),
                }
            )
        return pd.DataFrame(records).set_index("Mine")

    def get_anomalies_iqr(self, multiplier: float = 1.5) -> pd.DataFrame:
        def is_outlier(s):
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            return (s < (q1 - multiplier * iqr)) | (s > (q3 + multiplier * iqr))

        mask = self.df.groupby("Mine")["Production"].transform(is_outlier)
        return self.df[mask]

    def get_anomalies_zscore(self, threshold: float = 2.5) -> pd.DataFrame:
        def is_outlier(s):
            std = s.std()
            if std == 0 or pd.isna(std):
                return pd.Series(False, index=s.index)
            return ((s - s.mean()).abs() / std) > threshold

        mask = self.df.groupby("Mine")["Production"].transform(is_outlier)
        return self.df[mask]

    def get_anomalies_ma(
        self, window: int = 7, threshold_pct: float = 0.20
    ) -> pd.DataFrame:
        def is_outlier(s):
            ma = s.rolling(window=window, min_periods=1).mean()
            distance_pct = (s - ma).abs() / ma.replace(0, np.nan)
            return distance_pct > threshold_pct

        mask = self.df.groupby("Mine")["Production"].transform(is_outlier)
        return self.df[mask]

    def get_anomalies_grubbs(self, alpha: float = 0.05) -> pd.DataFrame:
        def is_outlier(s):
            s_work = s.dropna().copy()
            outlier_indices = []

            while len(s_work) >= 3:
                n = len(s_work)
                mean, std = s_work.mean(), s_work.std()
                if std == 0 or pd.isna(std):
                    break

                deviations = (s_work - mean).abs()
                max_idx = deviations.idxmax()
                g_calc = deviations.loc[max_idx] / std

                t_dist = stats.t.isf(alpha / (2 * n), n - 2)
                g_crit = ((n - 1) / np.sqrt(n)) * np.sqrt(
                    (t_dist**2) / (n - 2 + t_dist**2)
                )

                if g_calc > g_crit:
                    outlier_indices.append(max_idx)
                    s_work = s_work.drop(index=max_idx)
                else:
                    break

            return s.index.isin(outlier_indices)

        mask = self.df.groupby("Mine")["Production"].transform(is_outlier)
        return self.df[mask]
