"""
Pipeline complet de segmentation RFM — exécutable en ligne de commande.

Usage :
    python -m src.main

Nécessite le fichier de données dans data/raw/ (voir README).
"""
from .data_cleaning import load_data, quality_diagnostic, clean_transactions, detect_outliers_iqr
from .rfm import compute_rfm, score_rfm, build_segments, segment_summary
from .clustering import prepare_scaled_features, apply_kmeans
from .pareto import pareto_analysis
from .visualization import (
    plot_pareto_curve, plot_segment_contribution,
    plot_segment_map, plot_monthly_evolution,
)
from .reporting import generate_executive_summary


def run_pipeline(figures_dir: str = "reports/figures"):
    # 1. Chargement & diagnostic
    df = load_data()
    print(quality_diagnostic(df))

    # 2. Nettoyage
    df_clean = clean_transactions(df)
    outliers = detect_outliers_iqr(df_clean)
    print(f"Outliers IQR : {outliers['n_outliers']} lignes ({outliers['pct_outliers']:.2f}%)")

    # 3. RFM + scoring + segmentation métier
    rfm = compute_rfm(df_clean)
    rfm = score_rfm(rfm)
    rfm = build_segments(rfm)

    # 4. Segmentation alternative K-Means (validation)
    rfm_scaled = prepare_scaled_features(rfm)
    rfm = apply_kmeans(rfm, rfm_scaled, k_optimal=4)

    # 5. Pareto
    rfm_sorted, pareto_metrics = pareto_analysis(rfm)

    # 6. Résumé par segment
    summary = segment_summary(rfm)
    print(summary)

    # 7. Visuels
    plot_pareto_curve(rfm_sorted, save_path=f"{figures_dir}/pareto_curve.png")
    plot_segment_contribution(summary, save_path=f"{figures_dir}/segment_contribution.png")
    plot_segment_map(rfm, save_path=f"{figures_dir}/segment_map.png")

    df_clean_seg = df_clean.merge(rfm[["CustomerID", "Segment"]], on="CustomerID", how="left")
    plot_monthly_evolution(df_clean_seg, save_path=f"{figures_dir}/monthly_evolution.png")

    # 8. Synthèse exécutive
    summary_text = generate_executive_summary(
        rfm, df_clean, summary,
        pareto_metrics["pct_clients_80"], pareto_metrics["n_clients_80"],
    )
    print(summary_text)

    return rfm, summary, summary_text


if __name__ == "__main__":
    run_pipeline()
