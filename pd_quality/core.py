from __future__ import annotations

from typing import Optional

import pandas as pd

from .report import QualityReport, _in_notebook


def _comparison_key(value):
    """Make nested containers hashable while preserving their equality rules."""
    if isinstance(value, (list, tuple)):
        kind = list if isinstance(value, list) else tuple
        return kind, tuple(_comparison_key(item) for item in value)
    if isinstance(value, dict):
        return dict, frozenset(
            (_comparison_key(key), _comparison_key(item)) for key, item in value.items()
        )
    if isinstance(value, (set, frozenset)):
        return frozenset(_comparison_key(item) for item in value)
    return value


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
        try:
            duplicated = self._obj.duplicated()
        except TypeError:
            comparable = self._obj.apply(
                lambda col: col.map(_comparison_key) if col.dtype == object else col
            )
            duplicated = comparable.duplicated()
        return int(duplicated.sum())

    def check_types(self) -> pd.Series:
        """Return per-column dtypes."""
        return self._obj.dtypes

    def report(self, display: Optional[bool] = None) -> QualityReport:
        """Build a :class:`QualityReport`, optionally rendering it inline.

        Args:
            display: By default, print in a terminal and let Jupyter render
                the returned object. True explicitly displays the report;
                False skips explicit display.
        """
        missing_df = self.check_missing()
        memory_mb = self._obj.memory_usage(deep=True).sum() / (1024**2)
        constant_cols = []
        unique_cols = []
        for label, column in self._obj.items():
            try:
                distinct = column.nunique(dropna=True)
            except TypeError:
                distinct = column.map(_comparison_key).nunique(dropna=True)
            if distinct == 1:
                constant_cols.append(label)
            if distinct and distinct == len(column):
                unique_cols.append(label)

        report = QualityReport(
            shape=self._obj.shape,
            memory_mb=memory_mb,
            duplicates=self.check_duplicates(),
            missing=missing_df,
            dtypes_summary=self.check_types().value_counts(),
            constant_cols=constant_cols,
            unique_cols=unique_cols,
        )
        if display is True or (display is None and not _in_notebook()):
            report.display()
        return report
