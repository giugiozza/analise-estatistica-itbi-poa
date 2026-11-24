import html

import numpy as np
import pandas as pd
import streamlit as st

from charts import (
    plot_barras_horizontais,
    plot_grouped_property_type_shares,
    plot_overlay_area_histogram,
    plot_boxplot,
    plot_forest,
    plot_histograma_kde,
    plot_sparkline,
)
from data_loader import (
    add_property_type,
    descriptive_stats,
    load_frozen_sample,
    load_population,
    sample_and_inference,
)
from styles import inject_css


st.set_page_config(page_title="Análise Estatística — ITBI Porto Alegre", layout="wide")
inject_css()


@st.dialog("Sobre os dados", width="large")
def show_data_info() -> None:
    st.markdown(
        "**Fonte:** [Dados Abertos POA — ITBI](https://dadosabertos.poa.br/dataset/itbi)\n\n"
        "Registros de ITBI associados à transferência de imóveis em Porto Alegre/RS."
    )
    st.markdown(
        "**Objetivo desta análise**  \n"
        "Caracterizar o perfil das transferências imobiliárias registradas — incluindo área "
        "privativa e composição por finalidade — e comparar os resultados da população com "
        "uma amostra aleatória simples, estimando a média de área e a participação de apartamentos."
    )
    st.markdown(
        "**Período:** 2020–2026  \n"
        "**População:** 246.340 registros  \n"
        "**Variáveis:** 20 colunas  \n"
        f"**AAS congelada:** {fmt(len(frozen_sample), 0)} registros"
    )
    st.markdown(
        "**População de interesse**  \n"
        "Os registros consolidados de 2020 a 2026 com data de pagamento informada, que compõem "
        "a base analítica corrigida (246.340 linhas)."
    )
    st.markdown(
        "**Pré-tratamento dos dados**  \n"
        "A base bruta tinha 376.173 linhas e 21 variáveis. Foram removidas as linhas sem "
        "`data_pagamento` (129.831 registros), excluída a coluna `data_estimativa`, convertidos "
        "`cep`, `ano_construcao` e `n_zona_reg_imoveis` para tipos inteiros que aceitam ausências. "
        "Os demais valores ausentes foram mantidos. Uma revisão posterior confirmou duas áreas inválidas; "
        "foram removidas somente as linhas `_id=4437` (ano 2026, 6.796.319 m²) e `_id=52536` "
        "(ano 2024, 174.400 m²). Como `_id` se repete entre anos, a exclusão foi feita pela combinação "
        "de identificador, ano, guia e área. A base analítica resultante tem 246.340 linhas e 20 variáveis; "
        "não foi aplicada uma regra geral para outros valores altos de área."
    )
    st.markdown(
        "**Unidade amostral e sorteio**  \n"
        "Cada linha elegível da base analítica. A AAS foi sorteada sem reposição entre essas linhas; "
        "`numero_guia` pode se repetir, portanto uma linha não equivale necessariamente a uma guia única."
    )
    st.markdown(
        "**Variáveis selecionadas para a análise**  \n\n"
        "- **Quantitativa contínua — `area_constr_privativa`:** área construída de uso "
        "privativo atribuída à unidade imobiliária, medida em metros quadrados (m²). "
        "É usada para descrever a distribuição das áreas e estimar/testar a média populacional.\n"
        "- **Qualitativa nominal — `finalidade_construcao`:** categoria que indica a finalidade "
        "construtiva informada para o imóvel, isto é, sua vocação prevista, e não necessariamente "
        "o uso atual. As categorias são agrupadas em Apartamento, Casa, Box, Terreno e Outros; "
        "o evento do teste de proporção é o registro classificado como Apartamento."
    )
    st.markdown(
        "**Amostragem**  \n"
        f"AAS sem reposição, com seed 42 e {fmt(len(frozen_sample), 0)} linhas. "
        "O dimensionamento usa 95% de confiança "
        "e erro de planejamento de 5 pontos percentuais para a proporção; a precisão para a média "
        "é informada separadamente, considerando os casos válidos de área."
    )
    st.caption(
        (
            f"Registros válidos — AAS: {int(frozen_sample['area_constr_privativa'].notna().sum()):,} áreas e "
            f"{int(frozen_sample['finalidade_construcao'].notna().sum()):,} finalidades informadas; "
            f"população: {int(population['area_constr_privativa'].notna().sum()):,} áreas e "
            f"{int(population['finalidade_construcao'].notna().sum()):,} finalidades informadas."
        ).replace(",", ".")
    )


def fmt(value: float, decimals: int = 1, prefix: str = "", suffix: str = "") -> str:
    if value is None or not np.isfinite(value):
        return "—"
    text = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{prefix}{text}{suffix}"


@st.dialog("Informações da métrica", width="large")
def show_metric_info() -> None:
    info = st.session_state.get("metric_info")
    if not info:
        return

    st.markdown(f"### {info['title']}")
    st.markdown(info["description"])
    st.markdown(f"**Variável utilizada:** `{info['variable']}`")
    st.markdown(f"**Valor atual:** {info['value']}")
    if info.get("missing"):
        st.caption(info["missing"])


def render_kpis(stats: dict[str, float], sample: bool = False) -> None:
    labels = [
        ("Amostra AAS (n)" if sample else "População (N)", fmt(stats["n"], 0)),
        ("Área média" if sample else "Área média", fmt(stats["area_mean"], 2, suffix=" m²")),
        ("Mediana da área", fmt(stats["area_median"], 2, suffix=" m²")),
        ("Proporção de apartamentos", fmt(stats["apartment_share"] * 100, 2, suffix="%")),
    ]
    cols = st.columns(4)
    for i, (label, value) in enumerate(labels):
        with cols[i]:
            with st.container(border=True, key=f"kpi_{sample}_{i}", height=160):
                title_cols = st.columns([8, 1])
                with title_cols[0]:
                    st.markdown(
                        f'<div class="kpi-title">{html.escape(label)}</div>',
                        unsafe_allow_html=True,
                    )
                with title_cols[1]:
                    if st.button(
                        "ⓘ",
                        key=f"metric_info_{sample}_{i}",
                        help=f"Abrir explicação da métrica {label}",
                        use_container_width=True,
                    ):
                        metric_descriptions = [
                            {
                                "title": "Amostra AAS (n)" if sample else "População (N)",
                                "description": (
                                    "Quantidade de linhas da população analítica ou da amostra exibida."
                                    + (
                                        "\n\n**Seleção da amostra**\n\n"
                                        "- AAS sem reposição.\n"
                                        "- Seed `42`.\n"
                                        "- Confiança de 95%.\n"
                                        "- Erro de planejamento de 5 pontos percentuais para a proporção.\n"
                                        "- A precisão estimada para a média de área é calculada separadamente.\n"
                                        "- Observação: a amostra foi selecionada do conjunto contendo todas "
                                        "as linhas; cálculos posteriores excluem valores ausentes da variável "
                                        "analisada."
                                        "\n\n**Cálculo do tamanho da amostra**\n\n"
                                        "$$n = \\frac{\\frac{z^2p(1-p)}{e^2}}"
                                        "{1 + \\frac{z^2p(1-p)}{e^2N_{\\mathrm{validos}}}}$$\n\n"
                                        f"- \\(N_{{\\mathrm{{validos}}}}\\): "
                                        f"{int(load_population()['finalidade_construcao'].notna().sum()) if sample else int(stats['type_n']):,} registros com finalidade informada.\n".replace(",", ".")
                                        + r"- \(z\): 1,96 para confiança de 95%.\n"
                                        r"- \(p\): 0,50, proporção mais conservadora para máxima variabilidade.\n"
                                        r"- \(e\): 0,05, correspondente a 5 pontos percentuais.\n"
                                        "- O cálculo requer aproximadamente 384 casos válidos após a correção "
                                        "para população finita. A AAS congelada tem "
                                        f"{fmt(len(frozen_sample), 0)} linhas, das quais "
                                        f"{fmt(frozen_sample['finalidade_construcao'].notna().sum(), 0)} têm "
                                        "finalidade informada; a precisão efetiva aparece no dimensionamento."
                                        if sample
                                        else ""
                                    )
                                ),
                                "variable": "_id ou número de linhas do DataFrame",
                                "value": value,
                                "missing": None,
                            },
                            {
                                "title": "Área média",
                                "description": (
                                    "A média é obtida somando as áreas válidas e dividindo pelo número "
                                    "de registros com área informada.\n\n"
                                    "**Fórmula:** média = soma das áreas / quantidade de áreas válidas."
                                ),
                                "variable": "area_constr_privativa",
                                "value": value,
                                "missing": (
                                    f"Observações com área ausente não entram no cálculo "
                                    f"(n = {int(stats['area_n'])} áreas válidas)."
                                ),
                            },
                            {
                                "title": "Mediana da área",
                                "description": (
                                    "A mediana é o valor central das áreas após ordenação. Em uma "
                                    "amostra com quantidade par, corresponde à média dos dois valores centrais."
                                ),
                                "variable": "area_constr_privativa",
                                "value": value,
                                "missing": (
                                    f"Observações com área ausente não entram no cálculo "
                                    f"(n = {int(stats['area_n'])} áreas válidas)."
                                ),
                            },
                            {
                                "title": "Proporção de apartamentos",
                                "description": (
                                    "Percentual dos registros com finalidade de construção informada que "
                                    "foram classificados como apartamento.\n\n"
                                    "**Fórmula:** apartamentos / registros com finalidade informada × 100."
                                ),
                                "variable": "finalidade_construcao → tipo_imovel",
                                "value": value,
                                "missing": (
                                    f"Finalidades ausentes não entram no denominador; "
                                    f"n = {int(stats['type_n'])} registros com finalidade informada. "
                                    "Textos contendo “APARTAMENTO” são classificados como apartamento."
                                ),
                            },
                        ]
                        st.session_state["metric_info"] = metric_descriptions[i]
                        show_metric_info()
                st.markdown(f'<div class="kpi-value">{value}</div>', unsafe_allow_html=True)


def render_descriptive_table(
    stats: dict[str, float], df: pd.DataFrame, title: str, sample: bool = False
) -> None:
    area_rows = [
        ("Média", stats["area_mean"]),
        ("Mediana", stats["area_median"]),
        ("Desvio padrão", stats["area_std"]),
        ("Mínimo", stats["area_min"]),
        ("Máximo", stats["area_max"]),
    ]
    area_body = "".join(
        f"<tr><td>{label}</td><td>{fmt(value, 2, suffix=' m²')}</td>"
        f"<td>{fmt(stats['area_n'], 0)}</td></tr>"
        for label, value in area_rows
    )
    total = len(df)
    categories = ["Apartamento", "Casa", "Box", "Terreno", "Outros", "Não informado"]
    type_counts = df["tipo_imovel"].value_counts(dropna=False).reindex(categories, fill_value=0)
    type_body = "".join(
        f"<tr><td>{html.escape(category)}</td><td>{fmt(count, 0)}</td>"
        f"<td>{fmt(count / total * 100 if total else 0, 2, suffix='%')}</td></tr>"
        for category, count in type_counts.items()
    )
    area_export = pd.DataFrame(
        [
            {
                "Estatística": label,
                "Área privativa (m²)": fmt(value, 2, suffix=" m²"),
                "Registros válidos (n)": int(stats["area_n"]),
            }
            for label, value in area_rows
        ]
    )
    type_export = pd.DataFrame(
        [
            {
                "Tipo de imóvel": category,
                "Registros (n)": int(count),
                "Percentual do total (%)": (count / total * 100) if total else 0,
            }
            for category, count in type_counts.items()
        ]
    )
    suffix = "amostra" if sample else "populacao"

    with st.container(border=True):
        st.subheader(title)
        area_col, type_col = st.columns(2)
        with area_col:
            st.markdown("**Área privativa**")
            st.caption(f"Estatísticas calculadas sobre {fmt(stats['area_n'], 0)} áreas válidas.")
            st.markdown(
                '<table class="itbi-table"><thead><tr><th>Estatística</th>'
                '<th>Valor</th><th>n válido</th></tr></thead>'
                f"<tbody>{area_body}</tbody></table>",
                unsafe_allow_html=True,
            )
            st.download_button(
                "Exportar estatísticas de área (CSV)",
                area_export.to_csv(index=False).encode("utf-8-sig"),
                f"estatisticas_area_{suffix}.csv",
                "text/csv",
                key=f"download_{suffix}_area_stats",
                use_container_width=True,
            )
        with type_col:
            st.markdown("**Tipo de imóvel — finalidade da construção**")
            st.caption(
                f"{fmt(stats['type_n'], 0)} finalidades informadas; percentuais sobre as "
                f"{fmt(total, 0)} linhas do conjunto, incluindo “Não informado”."
            )
            st.markdown(
                '<table class="itbi-table"><thead><tr><th>Tipo de imóvel</th>'
                '<th>Registros</th><th>% do total</th></tr></thead>'
                f"<tbody>{type_body}</tbody></table>",
                unsafe_allow_html=True,
            )
            st.download_button(
                "Exportar composição por tipo (CSV)",
                type_export.to_csv(index=False).encode("utf-8-sig"),
                f"composicao_tipo_imovel_{suffix}.csv",
                "text/csv",
                key=f"download_{suffix}_type_stats",
                use_container_width=True,
            )

def render_descriptive_panel(df, title: str, color: str, sample: bool = False) -> None:
    stats = descriptive_stats(df)
    render_kpis(stats, sample)
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader(f"Distribuição da área construída privativa {'— Amostra' if sample else ''} (m²)")
            option = st.radio(
                "Controle dos extremos",
                ["Até o percentil 99,5%", "Todos os valores", "Faixa personalizada"],
                horizontal=True,
                key=f"histogram_range_{sample}",
            )
            area = df["area_constr_privativa"].dropna().astype(float)
            percentile_limit = float(area.quantile(0.995)) if len(area) else 0.0
            if option == "Até o percentil 99,5%" and len(area):
                display_area = area[area <= percentile_limit]
                range_caption = f"Curva limitada ao percentil 99,5% ({fmt(percentile_limit, 2)} m²)."
            elif option == "Faixa personalizada" and len(area):
                minimum = max(0, int(area.min()))
                maximum = max(minimum, int(np.ceil(area.max())))
                selected_range = st.slider(
                    "Faixa de área (m²)",
                    minimum,
                    maximum,
                    (minimum, maximum),
                    key=f"histogram_custom_range_{sample}",
                )
                display_area = area[area.between(selected_range[0], selected_range[1])]
                range_caption = (
                    f"Faixa personalizada: {fmt(selected_range[0], 0)}–"
                    f"{fmt(selected_range[1], 0)} m²."
                )
            else:
                display_area = area
                range_caption = "Todos os valores válidos estão incluídos."

            use_log_scale = st.checkbox(
                "Usar escala logarítmica",
                value=False,
                key=f"log_scale_{sample}",
            )
            histogram = plot_histograma_kde(display_area, color)
            if use_log_scale:
                histogram.update_xaxes(type="log")
            st.plotly_chart(
                histogram,
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"histogram_{sample}",
            )
            st.caption(
                f"{range_caption} Tamanho efetivo da área: "
                f"{int(display_area.count())} registros válidos."
            )
    with right:
        with st.container(border=True):
            st.subheader(f"Distribuição por tipo de imóvel {'— Amostra' if sample else ''}")
            st.plotly_chart(
                plot_barras_horizontais(df["tipo_imovel"].value_counts(), color),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"property_types_{sample}",
            )
            st.caption(
                "A finalidade original é agrupada em cinco tipos: Apartamento, Box, Terreno, Casa e Outros. "
                "Registros sem finalidade informada aparecem como categoria própria; os percentuais "
                "consideram todos os registros exibidos."
            )
    render_descriptive_table(stats, df, title, sample=sample)
    box_col, quartile_col = st.columns(2)
    area = df["area_constr_privativa"].dropna().astype(float)
    with box_col:
        with st.container(border=True):
            st.subheader("Boxplot da área construída privativa")
            st.plotly_chart(
                plot_boxplot(area, color),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"boxplot_{sample}",
            )
            limit = float(area.quantile(0.995)) if len(area) else 0.0
            excluded = int((area > limit).sum()) if len(area) else 0
            st.caption(
                f"Escala limitada ao percentil 99,5% ({fmt(limit, 2)} m²); "
                f"{excluded} outliers extremos foram excluídos desta visualização."
            )
    with quartile_col:
        with st.container(border=True):
            st.subheader("Quartis da área construída privativa")
            if len(area):
                quartiles = area.quantile([0.25, 0.50, 0.75])
                quartile_rows = [
                    ("Q1 — 25%", fmt(quartiles.loc[0.25], 2, suffix=" m²")),
                    ("Q2 — 50% / mediana", fmt(quartiles.loc[0.50], 2, suffix=" m²")),
                    ("Q3 — 75%", fmt(quartiles.loc[0.75], 2, suffix=" m²")),
                ]
                table_body = "".join(
                    f"<tr><td>{label}</td><td>{value}</td></tr>"
                    for label, value in quartile_rows
                )
                st.markdown(
                    '<table class="itbi-table">'
                    "<thead><tr><th>Quartil</th><th>Área</th></tr></thead>"
                    f"<tbody>{table_body}</tbody></table>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Não há áreas válidas para calcular os quartis.")


def render_sample_population_comparison(population: pd.DataFrame, sample: pd.DataFrame) -> None:
    population_area = population["area_constr_privativa"].dropna().astype(float)
    sample_area = sample["area_constr_privativa"].dropna().astype(float)
    population_types_valid = population["finalidade_construcao"].notna()
    sample_types_valid = sample["finalidade_construcao"].notna()
    population_type_n = int(population_types_valid.sum())
    sample_type_n = int(sample_types_valid.sum())
    population_apartment_share = (
        (population.loc[population_types_valid, "tipo_imovel"] == "Apartamento").mean()
        if population_type_n else np.nan
    )
    sample_apartment_share = (
        (sample.loc[sample_types_valid, "tipo_imovel"] == "Apartamento").mean()
        if sample_type_n else np.nan
    )

    def signed(value: float, decimals: int, suffix: str = "") -> str:
        if not np.isfinite(value):
            return "—"
        rendered = fmt(value, decimals, suffix=suffix)
        return f"+{rendered}" if value > 0 else rendered

    rows = []
    area_metrics = [
        ("Média da área (m²)", population_area.mean(), sample_area.mean(), 2),
        ("Mediana da área (m²)", population_area.median(), sample_area.median(), 2),
        ("Desvio padrão da área (m²)", population_area.std(ddof=1), sample_area.std(ddof=1), 2),
        ("Q1 — 25% da área (m²)", population_area.quantile(0.25), sample_area.quantile(0.25), 2),
        ("Q3 — 75% da área (m²)", population_area.quantile(0.75), sample_area.quantile(0.75), 2),
    ]
    for label, population_value, sample_value, decimals in area_metrics:
        difference = sample_value - population_value
        rows.append(
            f"<tr><td>{label}</td><td>{fmt(len(population_area), 0)}</td>"
            f"<td>{fmt(population_value, decimals, suffix=' m²')}</td>"
            f"<td>{fmt(len(sample_area), 0)}</td>"
            f"<td>{fmt(sample_value, decimals, suffix=' m²')}</td>"
            f"<td>{signed(difference, decimals, ' m²')}</td></tr>"
        )

    apartment_difference_pp = 100 * (sample_apartment_share - population_apartment_share)
    rows.append(
        f"<tr><td>Proporção de apartamentos (%)</td><td>{fmt(population_type_n, 0)}</td>"
        f"<td>{fmt(population_apartment_share * 100, 2, suffix='%')}</td>"
        f"<td>{fmt(sample_type_n, 0)}</td>"
        f"<td>{fmt(sample_apartment_share * 100, 2, suffix='%')}</td>"
        f"<td>{signed(apartment_difference_pp, 2, ' p.p.')}</td></tr>"
    )

    with st.container(border=True):
        st.subheader("Comparação entre população e AAS")
        st.caption(
            f"Conjuntos: população N={fmt(len(population), 0)}; AAS n={fmt(len(sample), 0)}. "
            "O n válido é calculado por medida: áreas não ausentes para estatísticas de área e "
            "finalidade informada para a proporção de apartamentos. Diferença = amostra − população."
        )
        table = (
            '<table class="itbi-table"><thead><tr><th>Medida</th>'
            '<th>n válido — população</th><th>População</th>'
            '<th>n válido — AAS</th><th>Amostra</th><th>Diferença AAS − população</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        )
        st.markdown(table, unsafe_allow_html=True)

        charts_left, charts_right = st.columns(2)
        with charts_left:
            chart_title, chart_info = st.columns([12, 1], vertical_alignment="center")
            with chart_title:
                st.markdown("**Distribuição de área — mesmas classes e escala**")
            with chart_info:
                with st.popover("ⓘ", help="Por que o desvio-padrão da população é maior?"):
                    population_sd = population_area.std(ddof=1)
                    sample_sd = sample_area.std(ddof=1)
                    population_large_n = int((population_area > 5000).sum())
                    sample_large_n = int((sample_area > 5000).sum())
                    population_sum_sq = ((population_area - population_area.mean()) ** 2).sum()
                    top_ten_sum_sq = (
                        (population_area.nlargest(min(10, len(population_area))) - population_area.mean()) ** 2
                    ).sum()
                    top_ten_share = top_ten_sum_sq / population_sum_sq if population_sum_sq else np.nan
                    st.markdown("**Por que os desvios-padrão diferem?**")
                    st.markdown(
                        f"O desvio-padrão é {fmt(population_sd, 2)} m² na população e "
                        f"{fmt(sample_sd, 2)} m² na AAS. Como os desvios são elevados ao quadrado, "
                        "poucos valores muito altos podem aumentar bastante essa medida."
                    )
                    st.markdown(
                        f"Acima de 5.000 m² há {fmt(population_large_n, 0)} registros entre "
                        f"{fmt(len(population_area), 0)} áreas válidas na população e "
                        f"{fmt(sample_large_n, 0)} entre {fmt(len(sample_area), 0)} na AAS. "
                        f"Os máximos são {fmt(population_area.max(), 2)} m² e "
                        f"{fmt(sample_area.max(), 2)} m², respectivamente."
                    )
                    st.caption(
                        f"Os dez maiores valores da população representam cerca de "
                        f"{fmt(top_ten_share * 100, 1)}% da soma dos desvios ao quadrado. "
                        "O corte P99,5 limita apenas a visualização; as estatísticas usam todas "
                        "as áreas válidas. Valores extremos devem ser validados antes de qualquer exclusão."
                    )
            area_limit = float(population_area.quantile(0.995)) if len(population_area) else 0.0
            if area_limit <= 0:
                area_limit = float(population_area.max()) if len(population_area) else 1.0
            population_display_n = int((population_area <= area_limit).sum())
            sample_display_n = int((sample_area <= area_limit).sum())
            st.plotly_chart(
                plot_overlay_area_histogram(population_area, sample_area, area_limit, bins=30),
                use_container_width=True,
                config={"displayModeBar": False},
                key="population_sample_area_overlay",
            )
            st.caption(
                f"Histograma normalizado, com 30 classes iguais de 0 a {fmt(area_limit, 2)} m². "
                "O teto é o P99,5 da população e é aplicado igualmente à AAS; "
                f"incluídos: {fmt(population_display_n, 0)} de {fmt(len(population_area), 0)} "
                f"áreas válidas na população e {fmt(sample_display_n, 0)} de "
                f"{fmt(len(sample_area), 0)} na AAS. Escala linear comum."
            )
        with charts_right:
            st.markdown("**Composição por tipo de imóvel — proporções**")
            st.plotly_chart(
                plot_grouped_property_type_shares(
                    population["tipo_imovel"].value_counts(),
                    sample["tipo_imovel"].value_counts(),
                    len(population),
                    len(sample),
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key="population_sample_property_type_comparison",
            )
            st.caption(
                "Cada barra usa o total de registros do conjunto como denominador. "
                "“Não informado” aparece como categoria própria; assim, as proporções incluem "
                "os registros sem finalidade e cada conjunto soma 100%."
            )


def format_pvalue(value: float) -> str:
    if not np.isfinite(value):
        return "—"
    return "< 0,001" if value < 0.001 else fmt(value, 4)


def test_decision_text(pvalue: float, alpha: float, alternative: str) -> str:
    if not np.isfinite(pvalue):
        return "Não há observações válidas suficientes para calcular este teste."
    if pvalue < alpha:
        return (
            f"Como p = {format_pvalue(pvalue)} < α = {alpha:.0%}, rejeitamos H₀. "
            f"A amostra fornece evidência estatística a favor de {alternative}."
        )
    return (
        f"Como p = {format_pvalue(pvalue)} ≥ α = {alpha:.0%}, não rejeitamos H₀. "
        f"A amostra não fornece evidência suficiente para concluir {alternative}; "
        "essa decisão não confirma H₀."
    )


def interval_reading(
    label: str,
    sample_estimate: float,
    population_parameter: float,
    interval: tuple[float, float],
    confidence: int,
    scale: float = 1,
    unit: str = "",
    difference_unit: str | None = None,
) -> str:
    lower, upper = interval
    contains = lower <= population_parameter <= upper
    relation = "contém" if contains else "não contém"
    delta_unit = difference_unit if difference_unit is not None else unit
    difference = sample_estimate - population_parameter
    return (
        f"{label}: a estimativa amostral é {fmt(sample_estimate * scale, 2, suffix=unit)} "
        f"e o parâmetro populacional conhecido é {fmt(population_parameter * scale, 2, suffix=unit)} "
        f"(diferença amostra − população: {fmt(difference * scale, 2, suffix=delta_unit)}). "
        f"O IC bilateral de {confidence}% [{fmt(lower * scale, 2, suffix=unit)}; "
        f"{fmt(upper * scale, 2, suffix=unit)}] {relation} o parâmetro populacional conhecido."
    )


def render_inference(df, frozen_sample, alpha: float, confidence: int) -> None:
    sample, result = sample_and_inference(df, frozen_sample, confidence=confidence, alpha=alpha)
    p_area = result["t_pvalue"]
    p_prop = result["z_pvalue"]
    reject_area = np.isfinite(p_area) and p_area < alpha
    reject_prop = np.isfinite(p_prop) and p_prop < alpha
    area_reading = interval_reading(
        "Média da área",
        result["sample"]["area_mean"],
        result["population"]["area_mean"],
        result["area_ci"],
        confidence,
        unit=" m²",
    )
    proportion_reading = interval_reading(
        "Proporção de apartamentos",
        result["sample"]["apartment_share"],
        result["population"]["apartment_share"],
        result["prop_ci"],
        confidence,
        scale=100,
        unit="%",
        difference_unit=" p.p.",
    )
    st.subheader("Testes de hipótese")
    st.caption(
        "O valor-p é a probabilidade, supondo H₀ e as condições do teste, de observar uma "
        "estatística tão ou mais extrema na direção de H₁. Compare-o com α; ele não é a "
        "probabilidade de H₀ ser verdadeira."
    )
    c1, c2 = st.columns(2)
    labels_area = ["Média amostral", f"{confidence}% IC", "Média populacional"]
    labels_prop = ["Proporção amostral", f"{confidence}% IC", "Proporção populacional"]
    with c1:
        with st.container(border=True):
            st.markdown("#### Teste de média: área construída privativa")
            st.markdown(
                '<div class="hypothesis">'
                '<div class="hypothesis-row"><strong>H₀: μ = 100 m²</strong>'
                '<span>A média populacional das áreas privativas declaradas é 100 m².</span></div>'
                '<div class="hypothesis-row"><strong>H₁: μ &lt; 100 m²</strong>'
                '<span>A média populacional está abaixo da referência de 100 m².</span></div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Referencial do estudo: 100 m² é um patamar redondo e fácil de interpretar "
                "para avaliar se a área média está abaixo desse valor; não é um limite normativo."
            )
            st.markdown(
                '<p class="market-reading"><strong>Leitura para o mercado:</strong> '
                'o teste pergunta se a área média dos registros com informação está abaixo '
                'de 100 m². A conclusão deve considerar o resultado amostral e a dispersão '
                'da variável.</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                plot_forest(
                    result["sample"]["area_mean"],
                    result["area_ci"],
                    result["population"]["area_mean"],
                    100,
                    labels_area,
                    confidence=confidence,
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key="forest_area",
            )
            badge = (
                "Teste indisponível" if not np.isfinite(p_area)
                else "Rejeitar H₀" if reject_area
                else "Não rejeitar H₀"
            )
            badge_class = "badge-reject" if reject_area else "badge-no-reject"
            st.markdown(
                f"t = {fmt(result['t_stat'], 3)} &nbsp; | &nbsp; p = {format_pvalue(p_area)} "
                f'<span class="{badge_class}">{badge}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Decisão:** {test_decision_text(p_area, alpha, 'que μ < 100 m²')}")
            st.caption(area_reading)
            st.caption(
                f"A conclusão considera n={int(result['sample']['area_n'])} áreas válidas, "
                f"α={alpha:.0%} e nível de confiança de {confidence}%. "
                f"O intervalo para a média usa t de Student com "
                f"{int(result['sample']['area_n']) - 1} graus de liberdade."
            )
    with c2:
        with st.container(border=True):
            st.markdown("#### Teste de proporção: apartamentos")
            st.markdown(
                '<div class="hypothesis">'
                '<div class="hypothesis-row"><strong>H₀: p = 50%</strong>'
                '<span>Metade dos registros com finalidade informada é classificada como apartamento.</span></div>'
                '<div class="hypothesis-row"><strong>H₁: p &gt; 50%</strong>'
                '<span>A participação de apartamentos supera metade dos registros com finalidade informada.</span></div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Referencial do estudo: 50% representa uma divisão igual entre apartamentos "
                "e as demais categorias; H₁ avalia se apartamentos formam a maioria. "
                "O dimensionamento também usa p = 0,50 por ser conservador quando a proporção é desconhecida."
            )
            st.markdown(
                '<p class="market-reading"><strong>Leitura para o mercado:</strong> '
                'o teste avalia se apartamentos são maioria entre os registros que têm '
                'finalidade de construção informada. '
                '<span class="scope-note">p é a proporção de apartamentos entre os registros '
                'com finalidade_construcao informada; ausentes não entram no denominador.</span></p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                plot_forest(
                    result["sample"]["apartment_share"],
                    result["prop_ci"],
                    result["population"]["apartment_share"],
                    0.5,
                    labels_prop,
                    percent=True,
                    confidence=confidence,
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key="forest_proportion",
            )
            badge = (
                "Teste indisponível" if not np.isfinite(p_prop)
                else "Rejeitar H₀" if reject_prop
                else "Não rejeitar H₀"
            )
            badge_class = "badge-reject" if reject_prop else "badge-no-reject"
            st.markdown(
                f"z = {fmt(result['z_stat'], 3)} &nbsp; | &nbsp; p = {format_pvalue(p_prop)} "
                f'<span class="{badge_class}">{badge}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Decisão:** {test_decision_text(p_prop, alpha, 'que p > 50%')}")
            st.caption(proportion_reading)
            st.caption(
                f"A conclusão considera n={int(sample['finalidade_construcao'].notna().sum())} "
                f"finalidades informadas, α={alpha:.0%} e nível de confiança de {confidence}%."
            )
    comparisons = [
        ("Área média (m²)", result["population"]["area_mean"], result["sample"]["area_mean"],
         result["area_ci"], False),
        ("Mediana da área (m²)", result["population"]["area_median"], result["sample"]["area_median"], None, False),
        ("Proporção de apartamentos", result["population"]["apartment_share"], result["sample"]["apartment_share"],
         result["prop_ci"], True),
    ]
    body = ""
    comparison_rows = []
    for label, pop, sam, ci, percent in comparisons:
        if ci:
            interval = f"[{fmt(ci[0] * (100 if percent else 1), 2)}{('%' if percent else ' m²')}; " \
                       f"{fmt(ci[1] * (100 if percent else 1), 2)}{('%' if percent else ' m²')}]"
            pop_value = pop * (100 if percent else 1)
            contains = ci[0] * (100 if percent else 1) <= pop_value <= ci[1] * (100 if percent else 1)
            contains_text = "Contém o parâmetro" if contains else "Não contém o parâmetro"
            contains_class = "check" if contains else "not-check"
        else:
            interval = "—"
            contains_text = "Intervalo não disponível"
            contains_class = "not-check"
        body += f"<tr><td>{label}</td><td>{fmt(pop * (100 if percent else 1), 2, suffix='%' if percent else ' m²')}</td>" \
                f"<td>{fmt(sam * (100 if percent else 1), 2, suffix='%' if percent else ' m²')}</td>" \
                f"<td>{interval}</td><td class='{contains_class}'>{contains_text}</td></tr>"
        comparison_rows.append({
            "Parâmetro": label,
            "População": fmt(pop * (100 if percent else 1), 2, suffix="%" if percent else " m²"),
            "Amostra": fmt(sam * (100 if percent else 1), 2, suffix="%" if percent else " m²"),
            "Intervalo de confiança": interval,
            "Resultado": contains_text,
        })
    with st.container(border=True):
        st.subheader("Comparação: população vs. estimativas amostrais")
        st.markdown(f'<table class="itbi-table"><thead><tr><th>Parâmetro</th><th>População</th>'
                    f'<th>Amostra</th><th>Intervalo de confiança</th><th>Contém parâmetro</th></tr></thead>'
                    f'<tbody>{body}</tbody></table>', unsafe_allow_html=True)
        st.download_button(
            "Exportar tabela comparativa (CSV)",
            pd.DataFrame(comparison_rows).to_csv(index=False).encode("utf-8-sig"),
            "comparacao_populacao_amostra.csv",
            "text/csv",
            key="download_comparison",
        )

    population_area = df["area_constr_privativa"].dropna().astype(float)
    sample_area = sample["area_constr_privativa"].dropna().astype(float)
    valid_population_types = int(df["finalidade_construcao"].notna().sum())
    sample_type_n = int(sample["finalidade_construcao"].notna().sum())
    sample_apartment_n = int((sample.loc[
        sample["finalidade_construcao"].notna(), "tipo_imovel"
    ] == "Apartamento").sum())
    sample_other_type_n = sample_type_n - sample_apartment_n
    area_above_1000 = int((population_area > 1000).sum())
    sample_fraction = sample_type_n / valid_population_types if valid_population_types else 0
    matching_two_sided_confidence = 100 * (1 - 2 * alpha)

    with st.expander("Condições e limitações da inferência", expanded=True):
        st.markdown(
            f"- **Dados válidos:** a AAS tem {fmt(len(sample), 0)} linhas; "
            f"os cálculos usam {fmt(len(sample_area), 0)} áreas informadas e "
            f"{fmt(sample_type_n, 0)} finalidades informadas. A proporção é definida entre "
            "registros com finalidade conhecida, então os ausentes ficam fora desse denominador.\n"
            f"- **Proporção:** o IC usa aproximação normal de Wald. Na amostra há "
            f"{fmt(sample_apartment_n, 0)} apartamentos e {fmt(sample_other_type_n, 0)} "
            "registros de outras categorias entre as finalidades informadas, contagens que "
            "sustentam essa aproximação neste conjunto.\n"
            f"- **Média da área:** na população, o desvio-padrão é "
            f"{fmt(result['population']['area_std'], 2)} m², o máximo é "
            f"{fmt(population_area.max(), 2)} m² e {fmt(area_above_1000, 0)} registros "
            "excedem 1.000 m². A cauda extrema pode afetar a média, o desvio-padrão e a "
            "aproximação do teste t. Examine a distribuição e faça análise de sensibilidade "
            "com critérios justificados; o recorte visual do histograma não exclui valores dos cálculos.\n"
            f"- **Plano amostral:** a fração de casos válidos da AAS em relação à população "
            f"elegível é {sample_fraction:.2%}. O teste e os ICs exibidos não aplicam correção "
            "para população finita; com essa fração, o efeito da correção é pequeno.\n"
            f"- **IC e teste:** o teste usa alternativa unilateral com α={alpha:.0%}; "
            f"o gráfico mostra IC bilateral de {confidence}%. Para equivalência direta com "
            f"esse teste, o IC bilateral correspondente seria {matching_two_sided_confidence:.0f}% "
            f"(ou um limite unilateral de {100 * (1 - alpha):.0f}%). Leia a decisão do teste "
            "pelo valor-p e α, e a inclusão do parâmetro conhecido como uma verificação separada.\n"
            f"- **Nível de confiança:** {confidence}% descreve a cobertura do método em "
            "repetidas AAS: sob as condições do procedimento, essa proporção dos intervalos "
            "construídos cobriria o parâmetro. Como a população inteira está disponível neste "
            "trabalho, podemos conferir se o intervalo desta amostra específica o contém."
        )


population = add_property_type(load_population())
frozen_sample = add_property_type(load_frozen_sample())
with st.sidebar:
    st.markdown("## Sobre a análise")
    with st.container(border=True):
        st.markdown("**Parâmetros da AAS**")
        st.markdown(
            "Confiança: **95%**  \n"
            f"AAS: **{fmt(len(frozen_sample), 0)} linhas** · Seed: **42**"
        )
    st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Sobre os dados", use_container_width=True, help="Abrir metadados e metodologia da base"):
        show_data_info()

st.markdown("# 📊 Análise Estatística — ITBI Porto Alegre")
st.caption(f"{len(population):,} registros na população analisada".replace(",", "."))


def render_quality(df: pd.DataFrame) -> None:
    area_missing = int(df["area_constr_privativa"].isna().sum())
    type_missing = int(df["finalidade_construcao"].isna().sum())
    total = len(df)
    area_valid = total - area_missing
    type_valid = total - type_missing
    area_coverage = (area_valid / total * 100) if total else 0
    type_coverage = (type_valid / total * 100) if total else 0

    with st.container(border=True):
        st.subheader("Qualidade dos dados na população em número de registros")
        q1, q2 = st.columns(2)
        q1.metric(
            "Área privativa — registros válidos",
            f"{area_valid:,}".replace(",", "."),
            f"{area_coverage:.1f}% do total",
            help="Contagem de registros com area_constr_privativa informada",
        )
        q2.metric(
            "Tipo de imóvel — registros válidos",
            f"{type_valid:,}".replace(",", "."),
            f"{type_coverage:.1f}% do total",
            help="Contagem de registros com finalidade_construcao informada",
        )


def render_sample_size_planning(df: pd.DataFrame) -> None:
    frozen_sample = load_frozen_sample()
    population_n = len(df)
    confidence_z = 1.96
    proportion_target = 0.50
    proportion_error = 0.05

    n0_proportion = confidence_z**2 * proportion_target * (1 - proportion_target) / proportion_error**2
    valid_type_n = int(df["finalidade_construcao"].notna().sum())
    type_coverage = valid_type_n / population_n if population_n else 0
    n_proportion_valid = (
        int(np.ceil(n0_proportion / (1 + (n0_proportion - 1) / valid_type_n)))
        if valid_type_n else 0
    )
    n_proportion_draw = (
        min(population_n, int(np.ceil(n_proportion_valid / type_coverage)))
        if type_coverage else population_n
    )

    valid_area = df["area_constr_privativa"].dropna().astype(float)
    valid_area_n = len(valid_area)
    area_sd = float(valid_area.std(ddof=1))
    sample_area_n = int(frozen_sample["area_constr_privativa"].notna().sum())
    sample_type_n = int(frozen_sample["finalidade_construcao"].notna().sum())
    sample_n = len(frozen_sample)

    # The finite-population correction uses the population of valid observations
    # for each variable; sample counts are the actual complete cases in the frozen AAS.
    area_fpc = (
        np.sqrt((valid_area_n - sample_area_n) / (valid_area_n - 1))
        if valid_area_n > 1 and sample_area_n <= valid_area_n else 0.0
    )
    area_margin = (
        confidence_z * area_sd / np.sqrt(sample_area_n) * area_fpc
        if sample_area_n else np.nan
    )
    type_fpc = (
        np.sqrt((valid_type_n - sample_type_n) / (valid_type_n - 1))
        if valid_type_n > 1 and sample_type_n <= valid_type_n else 0.0
    )
    proportion_margin = (
        confidence_z * np.sqrt(proportion_target * (1 - proportion_target) / sample_type_n) * type_fpc
        if sample_type_n else np.nan
    )
    valid_area_display = f"{valid_area_n:,}".replace(",", ".")
    valid_type_display = f"{valid_type_n:,}".replace(",", ".")
    n_proportion_valid_display = f"{n_proportion_valid:,}".replace(",", ".")
    n_proportion_draw_display = f"{n_proportion_draw:,}".replace(",", ".")
    sample_display = f"{sample_n:,}".replace(",", ".")

    with st.expander("Dimensionamento da amostra aleatória simples", expanded=False):
        st.markdown(
            "Para proporções, adota-se **95% de confiança** como equilíbrio entre segurança "
            "inferencial e tamanho viável, **erro máximo de 5 pontos percentuais** como precisão "
            "de planejamento para a participação de apartamentos e **p = 0,50** por maximizar "
            "\\(p(1-p)\\) quando essa proporção é desconhecida. O cálculo considera os registros "
            "com finalidade informada e ajusta o número de linhas sorteadas pela cobertura observada."
        )
        proportion_col, mean_col = st.columns(2)
        with proportion_col:
            st.markdown("**Estimativa de proporção**")
            st.metric("Linhas necessárias, ajustadas para ausências", n_proportion_draw_display)
            st.caption(
                f"São necessários {n_proportion_valid_display} registros com finalidade informada "
                f"(de {valid_type_display} na população); considerando cobertura de "
                f"{type_coverage:.1%}, o sorteio precisa de cerca de {n_proportion_draw_display} linhas. "
                f"Na AAS congelada, {sample_type_n} de {sample_n} linhas têm finalidade informada: "
                f"a margem máxima estimada é ±{fmt(proportion_margin * 100, 2, suffix=' p.p.')} "
                "a 95%, usando p = 0,50 e correção para população finita."
            )
            st.latex(r"n_0=\frac{z^2p(1-p)}{e^2},\qquad n=\frac{n_0}{1+(n_0-1)/N_{\mathrm{validos}}}")
        with mean_col:
            st.markdown("**Estimativa da média de área**")
            st.metric(
                "Margem estimada para a AAS congelada (95%)",
                f"±{fmt(area_margin, 1, suffix=' m²')}",
                f"{sample_area_n} áreas válidas em {sample_display} linhas",
            )
            st.caption(
                f"Estimativa de planejamento com desvio-padrão da população de {fmt(area_sd, 2)} m², "
                f"{valid_area_display} áreas válidas na população e correção para população finita. "
                "A margem é maior que a usada no planejamento da proporção porque a distribuição "
                "das áreas tem alta dispersão. O intervalo de confiança exibido no painel inferencial "
                "usa o desvio-padrão observado na AAS e pode, portanto, ter outra largura."
            )
            st.latex(r"E_{\bar{x}}=z\frac{S}{\sqrt{n_{\mathrm{validos}}}}\sqrt{\frac{N_{\mathrm{validos}}-n_{\mathrm{validos}}}{N_{\mathrm{validos}}-1}}")

        st.markdown(
            f"**AAS adotada:** {sample_display} linhas, sorteadas sem reposição. "
            f"Com os casos válidos observados ({sample_area_n} para área e {sample_type_n} para finalidade), "
            "a precisão estimada é apresentada separadamente para cada parâmetro; portanto, "
            "o erro de 5 pontos percentuais não é atribuído à estimativa da média."
        )


st.subheader("Visão geral da análise")
render_quality(population)

if "painel_ativo" not in st.session_state:
    st.session_state["painel_ativo"] = "População"

panel_options = [
    ("População", "population", "Painel 1 — População", "Indicadores, distribuições, quartis e estatísticas descritivas."),
    ("Amostra", "sample", "Painel 2 — Amostra", "AAS, indicadores amostrais e comparação visual."),
    ("Inferência", "inference", "Painel 3 — Inferência", "Intervalos, testes de média e proporção."),
]
nav_columns = st.columns(3)
for column, (panel_key, panel_slug, panel_title, panel_description) in zip(
    nav_columns, panel_options
):
    with column:
        is_active = st.session_state["painel_ativo"] == panel_key
        if st.button(
            f"**{panel_title}**  \n\n{panel_description}",
            key=f"panel_{panel_slug}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["painel_ativo"] = panel_key
            st.rerun()

if st.session_state["painel_ativo"] == "População":
    render_descriptive_panel(population, "Estatísticas descritivas da população", "#1849C6")
elif st.session_state["painel_ativo"] == "Amostra":
    st.caption(
        f"AAS sem reposição, selecionada da população completa com seed 42 "
        f"(n={fmt(len(frozen_sample), 0)} linhas)."
    )
    render_descriptive_panel(frozen_sample, "Estatísticas descritivas da amostra (AAS)", "#137C7E", True)
    render_sample_population_comparison(population, frozen_sample)
    render_sample_size_planning(population)
else:
    with st.container(border=True):
        st.markdown("**Parâmetros de inferência**")
        alpha_col, confidence_col = st.columns(2)
        with alpha_col:
            alpha = st.selectbox("Nível de significância (α)", [0.05, 0.01, 0.10], index=0)
        with confidence_col:
            confidence = st.slider("Confiança do intervalo", 80, 99, 95, format="%d%%")
    render_inference(population, frozen_sample, alpha, confidence)
