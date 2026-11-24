from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats


ROOT = Path(__file__).resolve().parent
POPULATION_PATH = ROOT / "itbi_poa_populacao.parquet"
SAMPLE_PATH = ROOT / "itbi_poa_amostra_aas.parquet"

# São necessários 384 casos válidos após a correção para população finita.
# Com cobertura de 95,51% na variável de proporção, o sorteio usa 403 linhas.
AAS_SIZE = 403


@st.cache_data
def load_population() -> pd.DataFrame:
    return pd.read_parquet(POPULATION_PATH)


@st.cache_data
def load_frozen_sample() -> pd.DataFrame:
    return pd.read_parquet(SAMPLE_PATH)


def classify_property(value: Any) -> str:
    if pd.isna(value):
        return "Não informado"
    text = str(value).upper()
    if "APARTAMENTO" in text:
        return "Apartamento"
    if "ESTACIONAMENTO" in text:
        return "Box"
    if "TERRENO" in text:
        return "Terreno"
    if "RESIDENCIA" in text:
        return "Casa"
    return "Outros"


@st.cache_data
def add_property_type(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["tipo_imovel"] = result["finalidade_construcao"].map(classify_property)
    return result


def filter_population(df: pd.DataFrame, years: tuple[int, int], property_type: str) -> pd.DataFrame:
    result = df[df["ano_referencia"].between(years[0], years[1])]
    if property_type != "Todos":
        result = result[result["tipo_imovel"] == property_type]
    return result


def descriptive_stats(df: pd.DataFrame) -> dict[str, float]:
    area = df["area_constr_privativa"].dropna()
    types = df.loc[df["finalidade_construcao"].notna(), "tipo_imovel"]
    return {
        "n": float(len(df)),
        "area_n": float(len(area)),
        "type_n": float(len(types)),
        "area_mean": float(area.mean()) if len(area) else np.nan,
        "area_median": float(area.median()) if len(area) else np.nan,
        "area_std": float(area.std()) if len(area) > 1 else np.nan,
        "area_min": float(area.min()) if len(area) else np.nan,
        "area_max": float(area.max()) if len(area) else np.nan,
        "apartment_share": float((types == "Apartamento").mean()) if len(types) else np.nan,
    }


def sample_and_inference(
    filtered: pd.DataFrame,
    frozen_sample: pd.DataFrame,
    seed: int = 42,
    confidence: int = 95,
    alpha: float = 0.05,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if len(filtered) == len(add_property_type(load_population())) and filtered.index.equals(
        add_property_type(load_population()).index
    ):
        sample = add_property_type(frozen_sample)
    else:
        sample = filtered.sample(min(AAS_SIZE, len(filtered)), random_state=seed).copy()
    sample_stats = descriptive_stats(sample)
    population_stats = descriptive_stats(filtered)
    level = confidence / 100
    area = sample["area_constr_privativa"].dropna()
    known_types = sample.loc[sample["finalidade_construcao"].notna(), "tipo_imovel"]
    proportion = (known_types == "Apartamento").astype(float)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    area_se = area.std(ddof=1) / np.sqrt(len(area)) if len(area) > 1 else np.nan
    t_critical = stats.t.ppf(1 - (1 - level) / 2, df=len(area) - 1) if len(area) > 1 else np.nan
    area_ci = (
        (area.mean() - t_critical * area_se, area.mean() + t_critical * area_se)
        if len(area) > 1
        else (np.nan, np.nan)
    )
    prop = proportion.mean() if len(proportion) else np.nan
    prop_se = np.sqrt(prop * (1 - prop) / len(proportion)) if len(proportion) else np.nan
    prop_ci = (prop - z * prop_se, prop + z * prop_se) if len(proportion) else (np.nan, np.nan)
    t_stat = (area.mean() - 100) / area_se if len(area) > 1 and area_se else np.nan
    z_stat = (prop - 0.5) / np.sqrt(0.5 * 0.5 / len(proportion)) if len(proportion) else np.nan
    return sample, {
        "sample": sample_stats,
        "population": population_stats,
        "area_ci": area_ci,
        "prop_ci": prop_ci,
        "t_stat": float(t_stat),
        "t_pvalue": float(stats.t.cdf(t_stat, len(area) - 1)) if len(area) > 1 else np.nan,
        "z_stat": float(z_stat),
        "z_pvalue": float(1 - stats.norm.cdf(z_stat)) if len(proportion) else np.nan,
        "alpha": alpha,
        "confidence": confidence,
    }
