"""
Démo interactive — Segmentation client RFM (Online Retail)

Lancer en local :
    streamlit run streamlit_app/app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Permet d'importer les modules du pipeline (src/) depuis la racine du repo
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data_cleaning import load_data, clean_transactions
from src.rfm import compute_rfm, score_rfm, build_segments, segment_summary
from src.clustering import prepare_scaled_features, elbow_inertias, apply_kmeans
from src.pareto import pareto_analysis

DEMO_DATA_PATH = ROOT / "data" / "processed" / "rfm_demo.csv"

st.set_page_config(
    page_title="Segmentation client RFM",
    page_icon="",
    layout="wide",
)

SEGMENT_COLORS = {
    "Champions": "#2F6F4E",
    "Clients fidèles": "#5B8C7B",
    "Clients réguliers": "#C98A3B",
    "Nouveaux clients": "#8DA6C7",
    "À risque (At Risk)": "#C97B3B",
    "Perdus (Hibernating)": "#A13D3D",
}

# ------------------------------------------------------------------
# Chargement des données
# ------------------------------------------------------------------
@st.cache_data
def load_demo_data() -> pd.DataFrame:
    return pd.read_csv("D:\\emman\\Desktop\\data\\onelineretail_analysis\\data\\processed\\rfm_demo.csv")


@st.cache_data(show_spinner="Nettoyage et calcul RFM sur le fichier importé…")
def compute_from_upload(file, k_optimal: int) -> pd.DataFrame:
    df = pd.read_excel(file) if file.name.endswith(("xlsx", "xls")) else pd.read_csv(file, encoding="ISO-8859-1")
    df_clean = clean_transactions(df)
    rfm = compute_rfm(df_clean)
    rfm = score_rfm(rfm)
    rfm = build_segments(rfm)
    scaled = prepare_scaled_features(rfm)
    rfm = apply_kmeans(rfm, scaled, k_optimal=k_optimal)
    return rfm


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
st.sidebar.title(" Segmentation RFM")
st.sidebar.caption("Démo interactive du projet — [voir le repo & l'étude de cas complète](https://github.com/)")

st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader(
    "Importer un autre fichier (optionnel)",
    type=["xlsx", "csv"],
    help="Même format que le dataset Online Retail : colonnes InvoiceNo, CustomerID, InvoiceDate, Quantity, UnitPrice.",
)

k_optimal = st.sidebar.slider("Nombre de clusters K-Means (k)", min_value=2, max_value=8, value=4)

if uploaded is not None:
    rfm = compute_from_upload(uploaded, k_optimal)
    st.sidebar.success(f"{len(rfm):,} clients recalculés depuis ton fichier.")
else:
    rfm = load_demo_data()
    if k_optimal != 4:
        scaled = prepare_scaled_features(rfm[["Recency", "Frequency", "Monetary"]])
        rfm = apply_kmeans(rfm, scaled, k_optimal=k_optimal)
    st.sidebar.info(f"Données de démonstration (Online Retail, {len(rfm):,} clients). Importe ton propre fichier pour recalculer en direct.")

segments_available = sorted(rfm["Segment"].unique())
segments_selected = st.sidebar.multiselect(
    "Filtrer par segment", segments_available, default=segments_available
)

rfm_filtered = rfm[rfm["Segment"].isin(segments_selected)]

# ------------------------------------------------------------------
# Header + KPIs
# ------------------------------------------------------------------
st.title("Qui sont les clients qui font vivre l'entreprise ?")
st.caption("Segmentation Récence · Fréquence · Montant — règles métier validées par un clustering K-Means.")

summary = segment_summary(rfm_filtered)
rfm_sorted, pareto_metrics = pareto_analysis(rfm_filtered)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clients (filtre actif)", f"{len(rfm_filtered):,}")
c2.metric("CA total", f"{rfm_filtered['Monetary'].sum():,.0f} ")
c3.metric("% clients → 80% du CA", f"{pareto_metrics['pct_clients_80']:.1f}%")
top_segment = summary["CA_Total"].idxmax() if len(summary) else "—"
c4.metric("Segment le plus rentable", top_segment)

st.markdown("---")

# ------------------------------------------------------------------
# Vue 1 — Contribution par segment
# ------------------------------------------------------------------
left, right = st.columns([1.1, 1])

with left:
    st.subheader("Contribution au chiffre d'affaires")
    summary_sorted = summary.sort_values("CA_Total", ascending=True).reset_index()
    fig_bar = px.bar(
        summary_sorted, x="CA_Total", y="Segment", orientation="h",
        color="Segment", color_discrete_map=SEGMENT_COLORS,
        text=summary_sorted["Pct_CA"].map(lambda x: f"{x:.1f}% du CA"),
        labels={"CA_Total": "Chiffre d'affaires (€)"},
    )
    fig_bar.update_layout(showlegend=False, height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.subheader("Cartographie des segments")
    seg_position = rfm_filtered.groupby("Segment").agg(
        Recency_moy=("Recency", "mean"),
        Frequency_moy=("Frequency", "mean"),
        Monetary_moy=("Monetary", "mean"),
        Nb_Clients=("CustomerID", "count"),
    ).reset_index()
    fig_scatter = px.scatter(
        seg_position, x="Recency_moy", y="Frequency_moy", size="Monetary_moy",
        color="Segment", color_discrete_map=SEGMENT_COLORS, text="Segment",
        labels={"Recency_moy": "Récence moyenne (jours)", "Frequency_moy": "Fréquence moyenne"},
        size_max=60,
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_xaxes(autorange="reversed")
    fig_scatter.update_layout(showlegend=False, height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------------
# Vue 2 — Pareto
# ------------------------------------------------------------------
st.subheader("Concentration du chiffre d'affaires (Pareto)")
rfm_sorted["ClientRank"] = range(1, len(rfm_sorted) + 1)
fig_pareto = px.line(
    rfm_sorted, x="ClientRank", y="CumPct",
    labels={"ClientRank": "Clients triés par CA décroissant", "CumPct": "% du CA cumulé"},
)
fig_pareto.add_hline(y=80, line_dash="dash", line_color="#A13D3D",
                      annotation_text="Seuil des 80%", annotation_position="bottom right")
fig_pareto.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig_pareto, use_container_width=True)

# ------------------------------------------------------------------
# Table + export
# ------------------------------------------------------------------
st.subheader("Détail par client")
st.dataframe(
    rfm_filtered[["CustomerID", "Recency", "Frequency", "Monetary", "Segment", "KMeans_Cluster"]]
    .sort_values("Monetary", ascending=False),
    use_container_width=True, height=320,
)

csv = rfm_filtered.to_csv(index=False).encode("utf-8")
st.download_button(" Télécharger la segmentation (CSV)", csv, "segmentation_rfm.csv", "text/csv")

st.markdown("---")
st.caption(
    "Démo construite avec le pipeline modulaire du repo (`src/`) — mêmes fonctions que le notebook d'analyse. "
    "Code source complet et étude de cas détaillée disponibles sur GitHub."
)
