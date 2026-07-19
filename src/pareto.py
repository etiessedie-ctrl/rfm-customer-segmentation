"""
Analyse de la concentration du chiffre d'affaires (loi de Pareto / 80-20).
"""
import pandas as pd


def pareto_analysis(rfm: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Trie les clients par CA décroissant et calcule le % de clients
    nécessaires pour atteindre 80% du chiffre d'affaires.

    Retourne (table triée avec cumuls, dict de métriques résumées).
    """
    rfm_sorted = rfm.sort_values("Monetary", ascending=False).reset_index(drop=True)
    rfm_sorted["CumMonetary"] = rfm_sorted["Monetary"].cumsum()
    rfm_sorted["CumPct"] = rfm_sorted["CumMonetary"] / rfm_sorted["Monetary"].sum() * 100
    rfm_sorted["ClientRank_Pct"] = (rfm_sorted.index + 1) / len(rfm_sorted) * 100

    clients_80pct = rfm_sorted[rfm_sorted["CumPct"] <= 80]
    n_clients_80 = len(clients_80pct) + 1  # +1 pour inclure le client qui franchit le seuil
    pct_clients_80 = n_clients_80 / len(rfm_sorted) * 100

    metrics = {
        "n_clients_80": n_clients_80,
        "n_clients_total": len(rfm_sorted),
        "pct_clients_80": pct_clients_80,
    }
    return rfm_sorted, metrics
