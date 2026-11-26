import pandas as pd
import numpy as np
import pytest
import pd_quality  # Importe ta librairie

def test_report_structure():
    # 1. Création d'un DF de test
    df = pd.DataFrame({
        'A': [1, 2, np.nan],
        'B': [1, 2, 1]
    })
    
    # 2. Exécution du rapport
    report = df.quality.report()
    
    # 3. Vérifications (Assertions)
    assert report['shape'] == (3, 2)
    assert report['missing_total'] == 1
    assert report['duplicates'] == 0
    assert 'memory_mb' in report


def test_duplicate_column_labels_are_checked_individually():
    df = pd.DataFrame([[1, 2], [1, 3], [1, 2]], columns=["a", "a"])
    report = df.quality.report(display=False)
    assert report.duplicates == 1
    assert report.constant_cols == ["a"]
    assert report.unique_cols == []
    assert report.missing.index.tolist() == ["a", "a"]
    assert df.iloc[:2].quality.report(display=False).unique_cols == ["a"]


def test_nested_containers_are_compared_by_content():
    first = {"a": [1, 2], "b": 3}
    reordered = {"b": 3, "a": [1, 2]}
    df = pd.DataFrame({
        "constant": [[first], [reordered], None],
        "varying": [[1, 2], [1, 2], (1, 2)],
    })
    original = df.copy()
    report = df.quality.report(display=False)
    assert df.quality.check_duplicates() == report.duplicates == 1
    assert report.constant_cols == ["constant"]
    assert report.missing.loc["constant", "Missing"] == 1
    assert report.unique_cols == []
    assert df.iloc[[0, 2]].quality.report(display=False).unique_cols == ["varying"]
    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize("values", [[], [None, None]])
def test_no_observed_value_is_neither_constant_nor_unique(values):
    report = pd.DataFrame({"empty": values}).quality.report(display=False)
    assert report.constant_cols == report.unique_cols == []
    assert report.missing.loc["empty", "Missing"] == len(values)


def test_labels_in_text_and_html():
    label = "<prix & taxe>"
    df = pd.DataFrame({0: [1, 2], label: [1, None]})
    report = df.quality.report(display=False)
    assert report.unique_cols == [0]
    assert "Colonnes 100% uniques : 0" in str(report)
    html = report._repr_html_()
    assert html.count("&lt;prix &amp; taxe&gt;") == 2
    assert label not in html
    assert "uniques (1) : 0" in html


def test_labels_in_rich():
    console = pytest.importorskip("rich.console").Console(width=120)
    report = pd.DataFrame({0: [1, 2], "[red]": [None, 1]}).quality.report(display=False)
    with console.capture() as captured:
        console.print(report)
    output = captured.get()
    assert output.count("[red]") == 2
    assert "uniques (1) : 0" in output



def test_notebook_leaves_default_rendering_to_jupyter(monkeypatch):
    import pd_quality.core as core

    rendered = []
    monkeypatch.setattr(core, "_in_notebook", lambda: True)
    monkeypatch.setattr(core.QualityReport, "display", lambda report: rendered.append(report))
    df = pd.DataFrame({"a": [1, 2]})

    report = df.quality.report()
    assert rendered == []
    assert "Rapport qualité" in report._repr_html_()
    explicit = df.quality.report(display=True)
    assert rendered == [explicit]
