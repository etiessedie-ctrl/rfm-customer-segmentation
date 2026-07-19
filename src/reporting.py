"""
Génération automatique de la synthèse exécutive à partir des indicateurs calculés.
"""
import pandas as pd


def generate_executive_summary(rfm_final: pd.DataFrame,
                                 df_clean: pd.DataFrame,
                                 segment_summary: pd.DataFrame,
                                 pct_clients_80: float,
                                 n_clients_80: int) -> str:
    """Construit le texte de synthèse exécutive (mêmes indicateurs que le notebook)."""
    top_segment = segment_summary["CA_Total"].idxmax()
    top_segment_pct_ca = segment_summary.loc[top_segment, "Pct_CA"]
    top_segment_pct_clients = segment_summary.loc[top_segment, "Pct_Clients"]

    at_risk_present = "À risque (At Risk)" in segment_summary.index
    at_risk_ca = segment_summary.loc["À risque (At Risk)", "CA_Total"] if at_risk_present else 0

    lines = [
        "=" * 70,
        "SYNTHÈSE EXÉCUTIVE — ANALYSE RFM ONLINE RETAIL",
        "=" * 70,
        f"• Base client exploitable : {rfm_final.shape[0]} clients ({df_clean.shape[0]} transactions valides)",
        f"• Pareto : {pct_clients_80:.1f}% des clients ({n_clients_80}) génèrent 80% du CA",
        f"• Segment le plus rentable : '{top_segment}' -> {top_segment_pct_ca:.1f}% du CA "
        f"pour seulement {top_segment_pct_clients:.1f}% des clients",
    ]
    if at_risk_present:
        lines.append(
            f"• Risque identifié : le segment 'À risque' représente encore {at_risk_ca:,.0f}€ de CA "
            f"historique à réactiver en priorité"
        )
    lines.append("=" * 70)
    return "\n".join(lines)
