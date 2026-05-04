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