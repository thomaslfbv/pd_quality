"""Rendering layer for pd_quality reports (rich, HTML, plain text)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RICH_AVAILABLE = False


def _in_notebook() -> bool:
    """Detect a Jupyter / IPython kernel context."""
    try:
        from IPython import get_ipython

        shell = get_ipython().__class__.__name__
        return shell == "ZMQInteractiveShell"
    except Exception:
        return False


def _bar(pct: float, width: int = 20) -> str:
    """Unicode horizontal bar (█/░) representing a percentage 0..100."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def _level(pct: float) -> str:
    """Severity level for a missing-value percentage."""
    if pct < 5:
        return "ok"
    if pct < 30:
        return "warn"
    return "crit"


_RICH_COLORS = {"ok": "green", "warn": "yellow", "crit": "red"}
_HTML_COLORS = {"ok": "#16a34a", "warn": "#d97706", "crit": "#dc2626"}


@dataclass
class QualityReport:
    """Structured quality report with multi-format rendering.

    Renders as a rich Panel group in terminals, HTML in Jupyter,
    and falls back to plain text everywhere else.
    """

    shape: tuple[int, int]
    memory_mb: float
    duplicates: int
    missing: pd.DataFrame  # cols: Missing, Percentage (%)
    dtypes_summary: pd.Series
    constant_cols: list[str] = field(default_factory=list)
    unique_cols: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ public

    def to_dict(self) -> dict[str, Any]:
        """Programmatic export (kept backward-compatible)."""
        return {
            "shape": self.shape,
            "missing_total": int(self.missing["Missing"].sum()),
            "duplicates": int(self.duplicates),
            "memory_mb": float(self.memory_mb),
            "constant_cols": list(self.constant_cols),
            "unique_cols": list(self.unique_cols),
        }

    def __getitem__(self, key: str) -> Any:
        """Backward-compatible dict access (e.g. ``report['shape']``)."""
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def display(self) -> "QualityReport":
        """Auto-render in the current environment, then return self."""
        if _in_notebook():
            from IPython.display import display as _display

            _display(self)
        elif _RICH_AVAILABLE:
            Console().print(self)
        else:
            print(str(self))
        return self

    # ----------------------------------------------------------------- rich

    def __rich__(self):  # noqa: D401 - rich protocol
        if not _RICH_AVAILABLE:  # pragma: no cover
            return str(self)

        rows, cols = self.shape
        dup_color = "red" if self.duplicates else "green"

        kpi = Table.grid(padding=(0, 3))
        for _ in range(4):
            kpi.add_column(justify="center")
        kpi.add_row(
            f"[bold]Lignes[/]\n[cyan]{rows:,}[/]",
            f"[bold]Colonnes[/]\n[cyan]{cols}[/]",
            f"[bold]Mémoire[/]\n[cyan]{self.memory_mb:.2f} MB[/]",
            f"[bold]Doublons[/]\n[{dup_color}]{self.duplicates}[/]",
        )
        overview = Panel(kpi, title="📊 Vue d'ensemble", border_style="blue")

        missing_panel = self._rich_missing_panel()
        types_panel = self._rich_types_panel()

        elements = [overview, missing_panel, types_panel]
        notes = self._rich_notes_panel()
        if notes is not None:
            elements.append(notes)
        return Group(*elements)

    def _rich_missing_panel(self):
        non_zero = self.missing[self.missing["Missing"] > 0].sort_values(
            "Percentage (%)", ascending=False
        )
        if non_zero.empty:
            return Panel(
                "[green]✓ Aucune valeur manquante[/]",
                title="🔍 Valeurs manquantes",
                border_style="green",
            )
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Colonne", style="white", no_wrap=True)
        table.add_column("Manquants", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Distribution", justify="left")
        for col, row in non_zero.iterrows():
            pct = float(row["Percentage (%)"])
            color = _RICH_COLORS[_level(pct)]
            table.add_row(
                str(col),
                f"{int(row['Missing']):,}",
                f"[{color}]{pct:.1f}%[/]",
                f"[{color}]{_bar(pct)}[/]",
            )
        return Panel(table, title="🔍 Valeurs manquantes", border_style="yellow")

    def _rich_types_panel(self):
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="bold magenta")
        grid.add_column(justify="right")
        for dtype, count in self.dtypes_summary.items():
            grid.add_row(str(dtype), f"{int(count)}")
        return Panel(grid, title="🏷️  Types", border_style="magenta")

    def _rich_notes_panel(self):
        notes = []
        if self.constant_cols:
            joined = ", ".join(self.constant_cols)
            notes.append(
                f"[yellow]⚠ Colonnes constantes ({len(self.constant_cols)})[/] : {joined}"
            )
        if self.unique_cols:
            joined = ", ".join(self.unique_cols)
            notes.append(
                f"[cyan]🔑 Colonnes 100% uniques ({len(self.unique_cols)})[/] : {joined}"
            )
        if not notes:
            return None
        return Panel("\n".join(notes), title="💡 Remarques", border_style="cyan")

    # ----------------------------------------------------------------- html

    def _repr_html_(self) -> str:
        rows, cols = self.shape
        dup_color = _HTML_COLORS["crit"] if self.duplicates else _HTML_COLORS["ok"]

        kpi_card = (
            "display:inline-block;min-width:140px;margin:4px;padding:10px 14px;"
            "border:1px solid #e5e7eb;border-radius:8px;text-align:center;"
            "font-family:system-ui,sans-serif;"
        )

        def card(label: str, value: str, color: str = "#0f172a") -> str:
            return (
                f'<div style="{kpi_card}">'
                f'<div style="font-size:11px;color:#64748b;text-transform:uppercase;">{label}</div>'
                f'<div style="font-size:20px;font-weight:600;color:{color};">{value}</div>'
                "</div>"
            )

        kpis = (
            card("Lignes", f"{rows:,}")
            + card("Colonnes", f"{cols}")
            + card("Mémoire", f"{self.memory_mb:.2f} MB")
            + card("Doublons", f"{self.duplicates}", dup_color)
        )

        missing_html = self._html_missing_section()
        types_html = self._html_types_section()
        notes_html = self._html_notes_section()

        return (
            '<div style="font-family:system-ui,sans-serif;color:#0f172a;">'
            '<h3 style="margin:6px 0;">📊 Rapport qualité</h3>'
            f'<div>{kpis}</div>'
            f"{missing_html}{types_html}{notes_html}"
            "</div>"
        )

    def _html_missing_section(self) -> str:
        non_zero = self.missing[self.missing["Missing"] > 0].sort_values(
            "Percentage (%)", ascending=False
        )
        if non_zero.empty:
            return (
                '<h4 style="margin:14px 0 6px;">🔍 Valeurs manquantes</h4>'
                '<div style="color:#16a34a;">✓ Aucune valeur manquante</div>'
            )
        rows_html = []
        for col, row in non_zero.iterrows():
            pct = float(row["Percentage (%)"])
            color = _HTML_COLORS[_level(pct)]
            bar = (
                '<div style="background:#f1f5f9;border-radius:4px;height:10px;width:160px;overflow:hidden;">'
                f'<div style="background:{color};height:100%;width:{pct:.1f}%;"></div>'
                "</div>"
            )
            rows_html.append(
                "<tr>"
                f'<td style="padding:4px 8px;">{col}</td>'
                f'<td style="padding:4px 8px;text-align:right;">{int(row["Missing"]):,}</td>'
                f'<td style="padding:4px 8px;text-align:right;color:{color};font-weight:600;">{pct:.1f}%</td>'
                f'<td style="padding:4px 8px;">{bar}</td>'
                "</tr>"
            )
        return (
            '<h4 style="margin:14px 0 6px;">🔍 Valeurs manquantes</h4>'
            '<table style="border-collapse:collapse;font-size:13px;">'
            '<thead><tr style="border-bottom:1px solid #e5e7eb;text-align:left;">'
            '<th style="padding:4px 8px;">Colonne</th>'
            '<th style="padding:4px 8px;text-align:right;">Manquants</th>'
            '<th style="padding:4px 8px;text-align:right;">%</th>'
            '<th style="padding:4px 8px;">Distribution</th>'
            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table>'
        )

    def _html_types_section(self) -> str:
        rows_html = "".join(
            f'<tr><td style="padding:2px 8px;color:#a21caf;">{dtype}</td>'
            f'<td style="padding:2px 8px;text-align:right;">{int(count)}</td></tr>'
            for dtype, count in self.dtypes_summary.items()
        )
        return (
            '<h4 style="margin:14px 0 6px;">🏷️ Types</h4>'
            f'<table style="border-collapse:collapse;font-size:13px;">{rows_html}</table>'
        )

    def _html_notes_section(self) -> str:
        parts = []
        if self.constant_cols:
            parts.append(
                f'<div style="color:#d97706;">⚠ Colonnes constantes ({len(self.constant_cols)}) : '
                f'{", ".join(self.constant_cols)}</div>'
            )
        if self.unique_cols:
            parts.append(
                f'<div style="color:#0891b2;">🔑 Colonnes 100% uniques ({len(self.unique_cols)}) : '
                f'{", ".join(self.unique_cols)}</div>'
            )
        if not parts:
            return ""
        return (
            '<h4 style="margin:14px 0 6px;">💡 Remarques</h4>'
            f'<div style="font-size:13px;">{"".join(parts)}</div>'
        )

    # ----------------------------------------------------------------- text

    def __str__(self) -> str:
        rows, cols = self.shape
        lines = [
            "=== RAPPORT DE QUALITÉ DES DONNÉES ===",
            f"Format            : {rows:,} lignes | {cols} colonnes",
            f"Utilisation mém.  : {self.memory_mb:.2f} MB",
            f"Lignes dupliquées : {self.duplicates}",
            "",
            "-- Valeurs manquantes --",
        ]
        non_zero = self.missing[self.missing["Missing"] > 0]
        if non_zero.empty:
            lines.append("Aucune valeur manquante.")
        else:
            lines.append(
                non_zero.sort_values("Percentage (%)", ascending=False).to_string()
            )
        lines += ["", "-- Types --", self.dtypes_summary.to_string()]
        if self.constant_cols:
            lines += ["", f"Colonnes constantes : {', '.join(self.constant_cols)}"]
        if self.unique_cols:
            lines += [f"Colonnes 100% uniques : {', '.join(self.unique_cols)}"]
        return "\n".join(lines)
