import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


def _layout(fig: go.Figure, x_title: str = "") -> go.Figure:
    fig.update_layout(
        height=300,
        margin=dict(l=12, r=12, t=15, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis_title=x_title,
        yaxis_title="Densidade",
        font=dict(color="#334155"),
    )
    return fig


def plot_histograma_kde(series: pd.Series, color: str, x_title: str = "Área construída privativa (m²)") -> go.Figure:
    values = series.dropna().astype(float)
    display = values
    fig = go.Figure(go.Histogram(x=display, histnorm="probability density", nbinsx=30,
                                 marker_color=color, marker_line_color="white", marker_line_width=1))
    if len(display) > 2 and display.nunique() > 1:
        x = np.linspace(display.min(), display.max(), 160)
        fig.add_trace(go.Scatter(x=x, y=gaussian_kde(display)(x), mode="lines",
                                 line=dict(color="#137C7E", width=2)))
    fig.update_xaxes(rangemode="tozero")
    if len(display):
        tick_values = np.linspace(float(display.min()), float(display.max()), 6)
        tick_text = [f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") for value in tick_values]
        fig.update_xaxes(tickvals=tick_values, ticktext=tick_text)
    return _layout(fig, x_title)


def plot_boxplot(series: pd.Series, color: str) -> go.Figure:
    values = series.dropna().astype(float)
    limit = float(values.quantile(0.995)) if len(values) else 0.0
    display = values[values <= limit] if len(values) else values
    q1 = float(display.quantile(0.25)) if len(display) else 0.0
    median = float(display.median()) if len(display) else 0.0
    q3 = float(display.quantile(0.75)) if len(display) else 0.0
    fig = go.Figure(
        go.Box(
            x=display,
            boxpoints=False,
            marker_color=color,
            line=dict(color=color),
            fillcolor="rgba(19,124,126,0.12)",
            name="Área privativa",
            hovertemplate=f"Área privativa<br>Q1: {q1:.2f} m²<br>"
                          f"Mediana: {median:.2f} m²<br>"
                          f"Q3: {q3:.2f} m²"
                          "<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, limit * 1.05] if limit > 0 else None)
    fig.update_layout(
        height=220,
        margin=dict(l=12, r=12, t=15, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis_title="Área construída privativa (m²)",
        yaxis_visible=False,
        font=dict(color="#334155"),
    )
    return fig


def plot_barras_horizontais(counts: pd.Series, color: str) -> go.Figure:
    ordered = counts.sort_values()
    total = int(ordered.sum())
    percentages = ordered / total * 100 if total else ordered * 0
    labels = [
        f"{int(count):,}".replace(",", ".") + f" ({percentage:.2f}%".replace(".", ",") + ")"
        for count, percentage in zip(ordered.values, percentages.values)
    ]
    hover_labels = [
        f"{int(count):,}".replace(",", ".") + f" — {percentage:.2f}%".replace(".", ",")
        for count, percentage in zip(ordered.values, percentages.values)
    ]
    fig = go.Figure(
        go.Bar(
            x=percentages.values,
            y=ordered.index,
            orientation="h",
            marker_color=color,
            text=labels,
            textposition="outside",
            cliponaxis=False,
            customdata=hover_labels,
            hovertemplate="%{y}<br>%{customdata}<extra></extra>",
        )
    )
    fig.update_layout(height=300, margin=dict(l=15, r=15, t=15, b=25),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#334155"), xaxis_title="Percentual (%)", yaxis_title="")
    tick_values = np.arange(0, 101, 20)
    tick_text = [f"{int(value)}%".replace(".", ",") for value in tick_values]
    fig.update_xaxes(tickvals=tick_values, ticktext=tick_text)
    return fig


def plot_overlay_area_histogram(
    population_area: pd.Series,
    sample_area: pd.Series,
    upper_limit: float,
    bins: int = 30,
) -> go.Figure:
    """Compare area distributions with identical bins, range, and normalization."""
    population_values = population_area.dropna().astype(float)
    sample_values = sample_area.dropna().astype(float)
    population_values = population_values[population_values <= upper_limit]
    sample_values = sample_values[sample_values <= upper_limit]
    bin_width = upper_limit / bins if upper_limit > 0 else 1

    fig = go.Figure()
    for values, name, color in (
        (population_values, "População", "#1849C6"),
        (sample_values, "AAS", "#137C7E"),
    ):
        fig.add_trace(
            go.Histogram(
                x=values,
                name=f"{name} (n={len(values):,})".replace(",", "."),
                histnorm="probability",
                xbins=dict(start=0, end=upper_limit, size=bin_width),
                marker=dict(color=color, line=dict(color="white", width=0.5)),
                opacity=0.55,
                hovertemplate="Faixa: %{x}<br>Fração nesta classe: %{y:.1%}<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        barmode="overlay",
        height=360,
        margin=dict(l=12, r=12, t=15, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155"),
        xaxis_title="Área construída privativa (m²)",
        yaxis_title="Fração dos registros em cada classe",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(range=[0, upper_limit], tickformat=",.0f", showgrid=False)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    return fig


def plot_grouped_property_type_shares(
    population_counts: pd.Series,
    sample_counts: pd.Series,
    population_n: int,
    sample_n: int,
) -> go.Figure:
    """Compare property-type shares with a common category order and denominator rule."""
    categories = ["Apartamento", "Casa", "Box", "Terreno", "Outros", "Não informado"]
    population_shares = population_counts.reindex(categories, fill_value=0) / population_n if population_n else 0
    sample_shares = sample_counts.reindex(categories, fill_value=0) / sample_n if sample_n else 0

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=categories,
            x=population_shares,
            name=f"População (N={population_n:,})".replace(",", "."),
            orientation="h",
            marker_color="#1849C6",
            customdata=population_counts.reindex(categories, fill_value=0).to_numpy(),
            hovertemplate="%{y}<br>Participação: %{x:.2%}<br>Registros: %{customdata:,}<extra>%{fullData.name}</extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=categories,
            x=sample_shares,
            name=f"AAS (n={sample_n:,})".replace(",", "."),
            orientation="h",
            marker_color="#137C7E",
            customdata=sample_counts.reindex(categories, fill_value=0).to_numpy(),
            hovertemplate="%{y}<br>Participação: %{x:.2%}<br>Registros: %{customdata:,}<extra>%{fullData.name}</extra>",
        )
    )
    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(l=12, r=12, t=15, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155"),
        xaxis_title="Participação do conjunto",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(tickformat=".0%", rangemode="tozero")
    fig.update_yaxes(autorange="reversed")
    return fig


def plot_sparkline(values: list[float], color: str) -> go.Figure:
    fig = go.Figure(go.Scatter(y=values, mode="lines", line=dict(color=color, width=2)))
    fig.update_layout(height=35, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", xaxis_visible=False, yaxis_visible=False)
    return fig


def plot_forest(sample_value: float, ci: tuple[float, float], population_value: float,
                h0: float, labels: list[str], percent: bool = False, confidence: int = 95) -> go.Figure:
    fmt = ".2%" if percent else ".2f"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[sample_value], y=[labels[0]], mode="markers+text",
                             text=[format(sample_value, fmt)], textposition="middle right",
                             marker=dict(size=10, color="#137C7E")))
    fig.add_trace(go.Scatter(x=list(ci), y=[labels[1], labels[1]], mode="lines",
                             line=dict(color="#137C7E", width=18)))
    fig.add_trace(go.Scatter(x=[population_value], y=[labels[2]], mode="markers",
                             marker=dict(symbol="diamond", size=11, color="#137C7E")))
    fig.add_vline(x=h0, line_dash="dash", line_color="#1849C6", line_width=2)
    fig.add_annotation(x=h0, y=1.16, yref="paper", text=format(h0, fmt), showarrow=False,
                       font=dict(color="#1849C6", size=12))
    fig.update_layout(height=260, margin=dict(l=12, r=20, t=25, b=15), showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(tickformat=".2%" if percent else ".2f"),
                      yaxis=dict(categoryorder="array", categoryarray=labels[::-1]),
                      font=dict(color="#334155"))
    return fig
