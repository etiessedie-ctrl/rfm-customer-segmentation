"""
Fonctions de visualisation : graphiques de qualité des données
et les 3 vues de restitution "COMEX" (segments, cartographie, évolution).
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


def plot_pareto_curve(rfm_sorted: pd.DataFrame, n_bins: int = 10, save_path: str = None):
    """Courbe de Pareto : CA par décile de clients + % cumulé."""
    rfm_sorted = rfm_sorted.copy()
    rfm_sorted["Decile"] = pd.qcut(rfm_sorted.index, n_bins, labels=[f"D{i+1}" for i in range(n_bins)])
    decile_ca = rfm_sorted.groupby("Decile")["Monetary"].sum()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(decile_ca.index, decile_ca.values, color="#4C72B0", label="CA par décile de clients")
    ax1.set_xlabel("Déciles de clients (D1 = plus gros contributeurs)")
    ax1.set_ylabel("Chiffre d'affaires (euro)", color="#4C72B0")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x/1000:.0f}k€"))

    ax2 = ax1.twinx()
    cum_pct = decile_ca.cumsum() / decile_ca.sum() * 100
    ax2.plot(cum_pct.index, cum_pct.values, color="#C44E52", marker="o", linewidth=2, label="% CA cumulé")
    ax2.axhline(80, color="gray", linestyle="--", linewidth=1)
    ax2.set_ylabel("% du CA cumulé", color="#C44E52")
    ax2.set_ylim(0, 105)

    plt.title("Courbe de Pareto — Concentration du chiffre d'affaires par client",
               fontsize=13, fontweight="bold")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_segment_contribution(segment_summary: pd.DataFrame, save_path: str = None):
    """Bar chart horizontal trié : contribution de chaque segment au CA."""
    summary = segment_summary.sort_values("CA_Total", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(summary.index, summary["CA_Total"], color="#55A868")
    for bar, pct in zip(bars, summary["Pct_CA"]):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f"  {pct:.1f}% du CA", va="center", fontsize=9)
    ax.set_xlabel("Chiffre d'affaires (€)")
    ax.set_title("Contribution de chaque segment au chiffre d'affaires total",
                 fontsize=13, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x/1000:.0f}k€"))
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_segment_map(rfm_segmented: pd.DataFrame, save_path: str = None):
    """Scatter Récence x Fréquence, taille = Montant moyen, par segment."""
    seg_position = rfm_segmented.groupby("Segment").agg(
        Recency_moy=("Recency", "mean"),
        Frequency_moy=("Frequency", "mean"),
        Monetary_moy=("Monetary", "mean"),
        Nb_Clients=("CustomerID", "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(
        seg_position["Recency_moy"], seg_position["Frequency_moy"],
        s=seg_position["Monetary_moy"] / seg_position["Monetary_moy"].max() * 3000,
        c=range(len(seg_position)), cmap="viridis", alpha=0.7, edgecolors="black",
    )
    for _, row in seg_position.iterrows():
        ax.annotate(row["Segment"], (row["Recency_moy"], row["Frequency_moy"]),
                     textcoords="offset points", xytext=(0, 12),
                     ha="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Récence moyenne (jours depuis dernier achat) — plus bas = mieux")
    ax.set_ylabel("Fréquence moyenne (nb commandes)")
    ax.set_title("Cartographie des segments clients\n(taille des bulles = montant moyen dépensé)",
                 fontsize=13, fontweight="bold")
    ax.invert_xaxis()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_monthly_evolution(df_clean_with_segment: pd.DataFrame, save_path: str = None):
    """Évolution mensuelle du CA par segment."""
    df = df_clean_with_segment.copy()
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    monthly_ca = df.groupby(["YearMonth", "Segment"])["TotalPrice"].sum().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(11, 6))
    monthly_ca.plot(ax=ax, marker="o", linewidth=2)
    ax.set_title("Évolution mensuelle du chiffre d'affaires par segment",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Chiffre d'affaires (€)")
    ax.set_xlabel("Mois")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x/1000:.0f}k€"))
    plt.xticks(rotation=45)
    ax.legend(title="Segment", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
