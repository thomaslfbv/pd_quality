import pandas as pd

from .report import QualityReport


@pd.api.extensions.register_dataframe_accessor("quality")
class QualityAnalyzer:
    """Pandas accessor exposing quality-check helpers under ``df.quality``."""

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        self._obj = pandas_obj

    def check_missing(self) -> pd.DataFrame:
        """Per-column missing-value count and percentage."""
        missing = self._obj.isnull().sum()
        percent = (missing / len(self._obj)) * 100 if len(self._obj) else missing * 0
        return pd.DataFrame({"Missing": missing, "Percentage (%)": percent.round(2)})

    def check_duplicates(self) -> int:
        """Count fully duplicated rows."""
        return int(self._obj.duplicated().sum())

    def check_types(self) -> pd.Series:
        """Return per-column dtypes."""
        return self._obj.dtypes

    def _constant_columns(self) -> list[str]:
        """Columns with a single unique non-null value."""
        return [c for c in self._obj.columns if self._obj[c].nunique(dropna=True) <= 1]

    def _unique_columns(self) -> list[str]:
        """Columns where every non-null value is unique (primary-key candidates)."""
        n = len(self._obj)
        if n == 0:
            return []
        return [
            c
            for c in self._obj.columns
            if self._obj[c].notna().all() and self._obj[c].nunique() == n
        ]

    def report(self, display: bool = True) -> QualityReport:
        """Build a :class:`QualityReport`, optionally rendering it inline.

        Args:
            display: When True (default), auto-render the report in the
                current environment (rich in terminals, HTML in Jupyter).
                Set False to silently return the report object.
        """
        missing_df = self.check_missing()
        memory_mb = self._obj.memory_usage(deep=True).sum() / (1024**2)
        report = QualityReport(
            shape=self._obj.shape,
            memory_mb=memory_mb,
            duplicates=self.check_duplicates(),
            missing=missing_df,
            dtypes_summary=self.check_types().value_counts(),
            constant_cols=self._constant_columns(),
            unique_cols=self._unique_columns(),
        )
        if display:
            report.display()
        return report
