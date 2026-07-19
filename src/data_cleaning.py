"""
Chargement et nettoyage des transactions brutes.
"""
import os
import pandas as pd


def load_data(path_xlsx: str = "data/raw/Online Retail.xlsx",
              path_csv: str = "data/raw/Online Retail.csv") -> pd.DataFrame:
    """Charge le dataset brut depuis un .xlsx ou un .csv (fallback)."""
    if os.path.exists(path_xlsx):
        return pd.read_excel(path_xlsx)
    if os.path.exists(path_csv):
        return pd.read_csv(path_csv, encoding="ISO-8859-1")
    raise FileNotFoundError(
        f"Aucun fichier trouvé ({path_xlsx} ou {path_csv}). "
        "Placez le fichier source dans data/raw/."
    )


def quality_diagnostic(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne un tableau de diagnostic qualité AVANT nettoyage."""
    n_total = len(df)
    n_na_customer = df["CustomerID"].isna().sum()
    n_cancel = df["InvoiceNo"].astype(str).str.startswith("C").sum()
    n_neg_qty = (df["Quantity"] <= 0).sum()
    n_neg_price = (df["UnitPrice"] <= 0).sum()

    return pd.DataFrame({
        "Problème": ["Total lignes", "CustomerID manquant",
                     "Annulations (InvoiceNo commence par C)",
                     "Quantité <= 0", "Prix unitaire <= 0"],
        "Nombre de lignes": [n_total, n_na_customer, n_cancel, n_neg_qty, n_neg_price],
        "% du total": [
            100,
            round(n_na_customer / n_total * 100, 1),
            round(n_cancel / n_total * 100, 1),
            round(n_neg_qty / n_total * 100, 1),
            round(n_neg_price / n_total * 100, 1),
        ],
    })


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie le dataset brut :
    - supprime les lignes sans CustomerID
    - supprime les annulations (InvoiceNo commençant par 'C')
    - supprime les quantités/prix <= 0
    - calcule TotalPrice et type les colonnes
    """
    df_clean = df.copy()
    df_clean = df_clean.dropna(subset=["CustomerID"])
    df_clean = df_clean[~df_clean["InvoiceNo"].astype(str).str.startswith("C")]
    df_clean = df_clean[(df_clean["Quantity"] > 0) & (df_clean["UnitPrice"] > 0)]

    df_clean["InvoiceDate"] = pd.to_datetime(df_clean["InvoiceDate"])
    df_clean["TotalPrice"] = df_clean["Quantity"] * df_clean["UnitPrice"]
    df_clean["CustomerID"] = df_clean["CustomerID"].astype(int)

    return df_clean


def detect_outliers_iqr(df_clean: pd.DataFrame, column: str = "TotalPrice") -> dict:
    """Détecte les valeurs aberrantes via la méthode IQR sur une colonne donnée."""
    q1, q3 = df_clean[column].quantile([0.25, 0.75])
    iqr = q3 - q1
    seuil_haut = q3 + 1.5 * iqr
    n_outliers = (df_clean[column] > seuil_haut).sum()
    return {
        "seuil_haut": seuil_haut,
        "n_outliers": n_outliers,
        "pct_outliers": n_outliers / len(df_clean) * 100,
    }
