"""
Construction de la table RFM (Récence / Fréquence / Montant),
scoring en quintiles et segmentation métier.
"""
from datetime import timedelta
import pandas as pd


def compute_rfm(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Calcule Récence, Fréquence et Montant par client."""
    snapshot_date = df_clean["InvoiceDate"].max() + timedelta(days=1)

    rfm = df_clean.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
    ).reset_index()

    return rfm


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les scores en quintiles (1 à 5) pour R, F, M."""
    rfm = rfm.copy()
    rfm["R_score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["M_score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["RFM_Score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
    rfm["RFM_Segment_Code"] = (
        rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)
    )
    return rfm


def assign_segment(row: pd.Series) -> str:
    """Règle métier de segmentation basée sur les scores R et F."""
    r, f = row["R_score"], row["F_score"]
    if r >= 4 and f >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Clients fidèles"
    elif r >= 4 and f <= 2:
        return "Nouveaux clients"
    elif r <= 2 and f >= 4:
        return "À risque (At Risk)"
    elif r <= 2 and f <= 2:
        return "Perdus (Hibernating)"
    else:
        return "Clients réguliers"


def build_segments(rfm_scored: pd.DataFrame) -> pd.DataFrame:
    """Applique assign_segment sur toute la table RFM scorée."""
    rfm_scored = rfm_scored.copy()
    rfm_scored["Segment"] = rfm_scored.apply(assign_segment, axis=1)
    return rfm_scored


def segment_summary(rfm_segmented: pd.DataFrame) -> pd.DataFrame:
    """Agrège CA, nb clients et panier moyen par segment, avec % du total."""
    summary = rfm_segmented.groupby("Segment").agg(
        Nb_Clients=("CustomerID", "count"),
        CA_Total=("Monetary", "sum"),
        Panier_Moyen=("Monetary", "mean"),
    ).sort_values("CA_Total", ascending=False)

    summary["Pct_CA"] = summary["CA_Total"] / summary["CA_Total"].sum() * 100
    summary["Pct_Clients"] = summary["Nb_Clients"] / summary["Nb_Clients"].sum() * 100
    return summary
