"""
Segmentation alternative non supervisée (K-Means) sur les variables RFM.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


def prepare_scaled_features(rfm: pd.DataFrame) -> np.ndarray:
    """Log-transforme puis standardise Recency/Frequency/Monetary."""
    rfm_log = rfm[["Recency", "Frequency", "Monetary"]].apply(lambda x: np.log1p(x))
    scaler = StandardScaler()
    return scaler.fit_transform(rfm_log)


def elbow_inertias(rfm_scaled: np.ndarray, k_range=range(2, 9)) -> dict:
    """Calcule l'inertie K-Means pour chaque k (méthode du coude)."""
    inertias = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(rfm_scaled)
        inertias[k] = km.inertia_
    return inertias


def apply_kmeans(rfm: pd.DataFrame, rfm_scaled: np.ndarray, k_optimal: int = 4) -> pd.DataFrame:
    """Applique le K-Means avec k_optimal et ajoute la colonne de cluster."""
    rfm = rfm.copy()
    kmeans = KMeans(n_clusters=k_optimal, random_state=42, n_init=10)
    rfm["KMeans_Cluster"] = kmeans.fit_predict(rfm_scaled)
    return rfm
