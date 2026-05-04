import pandas as pd
import numpy as np

@pd.api.extensions.register_dataframe_accessor("quality")
class QualityAnalyzer:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def check_missing(self):
        """Calcule le taux de valeurs manquantes par colonne."""
        missing = self._obj.isnull().sum()
        percent = (missing / len(self._obj)) * 100
        return pd.DataFrame({'Missing': missing, 'Percentage (%)': percent.round(2)})

    def check_duplicates(self):
        """Compte les lignes totalement dupliquées."""
        return self._obj.duplicated().sum()

    def check_types(self):
        """Analyse la cohérence des types de données."""
        return self._obj.dtypes

    def report(self):
        """Génère un mini-rapport textuel et statistique."""
        missing_df = self.check_missing()
        dupes = self.check_duplicates()
        mem = self._obj.memory_usage(deep=True).sum() / (1024**2) # MB
        
        print("--- RAPPORT DE QUALITÉ DES DONNÉES ---")
        print(f"Format : {self._obj.shape[0]} lignes | {self._obj.shape[1]} colonnes")
        print(f"Utilisation Mémoire : {mem:.2f} MB")
        print(f"Lignes dupliquées : {dupes}")
        print("\n--- Analyse des valeurs manquantes ---")
        print(missing_df[missing_df['Missing'] > 0] if missing_df['Missing'].any() else "Aucune valeur manquante.")
        print("\n--- Aperçu des types ---")
        print(self.check_types().value_counts())
        print("--------------------------------------")

        # Retourne un dictionnaire pour exploitation programmatique
        return {
            "shape": self._obj.shape,
            "missing_total": missing_df['Missing'].sum(),
            "duplicates": dupes,
            "memory_mb": mem
        }