"""Plotly chart theme helper untuk Decidiq — Dark Premium theme."""
from typing import List, Optional

import plotly.graph_objects as go
import plotly.io as pio


# ==================== COLOR PALETTE — DARK ====================
COLORS = {
    "primary": "#a489ff",
    "primary_dark": "#8163ec",
    "primary_light": "#c4aaff",
    "accent": "#71d5e9",
    "accent_dark": "#4ec4dc",
    "success": "#77edb4",
    "warning": "#f7d578",
    "danger": "#ff9eaa",
    "info": "#71d5e9",
    "text": "#f5f6ff",
    "text_muted": "#adb6d5",
    "text_axis": "#aeb7d6",
    "grid": "#303451",
    "bg": "rgba(0,0,0,0)",
    "card_bg": "#1a1d3d",
    "card_border": "#343858",
    "line": "#343858",
}

CATEGORY_COLORS = [
    "#a489ff", "#71d5e9", "#77edb4", "#f7d578",
    "#ff9eaa", "#ec3f92", "#c4aaff", "#89d84a",
]


# ==================== THEME ====================
def apply_theme(fig: go.Figure, height: Optional[int] = None) -> go.Figure:
    """Apply Decidiq dark theme ke Plotly figure."""
    fig.update_layout(
        font=dict(
            family="DM Sans, -apple-system, BlinkMacSystemFont, sans-serif",
            size=12,
            color=COLORS["text"],
        ),
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        margin=dict(t=30, b=60, l=60, r=30),
        hoverlabel=dict(
            bgcolor="#302650",
            font_size=12,
            font_family="DM Sans, sans-serif",
            font_color="#ffffff",
            bordercolor=COLORS["primary"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=COLORS["text_axis"], family="DM Sans"),
            bgcolor="rgba(26, 29, 61, 0.6)",
            bordercolor=COLORS["card_border"],
            borderwidth=1,
            itemsizing="constant",
        ),
        xaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(color=COLORS["text_axis"], size=11, family="DM Sans"),
            title=dict(
                font=dict(color=COLORS["text"], size=12,
                          family="DM Sans"),
            ),
            zeroline=False,
            linecolor=COLORS["line"],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS["grid"],
            gridwidth=1,
            showline=False,
            tickfont=dict(color=COLORS["text_axis"], size=11, family="DM Sans"),
            title=dict(
                font=dict(color=COLORS["text"], size=12,
                          family="DM Sans"),
            ),
            zeroline=False,
        ),
    )
    if height:
        fig.update_layout(height=height)
    return fig


# ==================== LINE ====================
def line_chart(fig: go.Figure, height: int = 320,
               y_title: str = "", x_title: str = "") -> go.Figure:
    """Theme line chart dengan smooth curve."""
    fig.update_traces(
        line=dict(width=3, shape="spline", smoothing=0.5),
    )
    fig = apply_theme(fig, height=height)
    fig.update_layout(
        yaxis_title=dict(text=f"<b>{y_title}</b>", font=dict(size=12)),
        xaxis_title=dict(text=f"<b>{x_title}</b>", font=dict(size=12)),
    )
    return fig


# ==================== BAR ====================
def bar_chart(fig: go.Figure, height: int = 340, show_values: bool = True,
              y_title: str = "", x_title: str = "") -> go.Figure:
    """Theme bar chart dengan nilai di atas bar."""
    fig.update_traces(marker_line_width=0)

    if show_values:
        for trace in fig.data:
            if hasattr(trace, "text") and trace.text is None:
                trace.text = trace.y
                trace.textposition = "outside"
                trace.textfont = dict(
                    size=11, color=COLORS["text"], family="DM Sans",
                )
                trace.cliponaxis = False

    fig = apply_theme(fig, height=height)
    fig.update_layout(
        yaxis_title=dict(text=f"<b>{y_title}</b>", font=dict(size=12)),
        xaxis_title=dict(text=f"<b>{x_title}</b>", font=dict(size=12)),
        bargap=0.35,
    )
    return fig


# ==================== PIE ====================
def pie_chart(fig: go.Figure, height: int = 340,
              center_text: str = "") -> go.Figure:
    """Theme pie/donut chart — dark friendly."""
    fig.update_traces(
        textfont=dict(size=11, color="#ffffff", family="DM Sans"),
        marker=dict(
            line=dict(color="#0d1026", width=3),
            colors=CATEGORY_COLORS,
        ),
        hole=0.55,
    )

    if center_text:
        fig.add_annotation(
            text=f"<b>{center_text}</b>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=COLORS["text"], family="DM Sans"),
        )

    fig = apply_theme(fig, height=height)
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle", y=0.5,
            xanchor="left", x=1.02,
            font=dict(size=11, color=COLORS["text_axis"], family="DM Sans"),
            bgcolor="rgba(26, 29, 61, 0.6)",
            bordercolor=COLORS["card_border"],
            borderwidth=1,
        ),
    )
    return fig


# ==================== GAUGE ====================
def gauge(fig_title: str, value: float, target: float,
          min_val: float = 0, max_val: float = 100,
          unit: str = "%", higher_is_better: bool = True,
          height: int = 220) -> go.Figure:
    """Buat gauge chart untuk KPI vs target — dark theme."""
    met = (value >= target) if higher_is_better else (value <= target)
    bar_color = COLORS["success"] if met else COLORS["danger"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"<b>{fig_title}</b>",
               "font": {"size": 13, "color": COLORS["text_axis"], "family": "DM Sans"}},
        number={
            "suffix": unit,
            "font": {"size": 28, "color": COLORS["text"], "family": "DM Sans"},
        },
        delta={
            "reference": target,
            "increasing": {"color": COLORS["success"]},
            "decreasing": {"color": COLORS["danger"]},
            "font": {"size": 12, "family": "DM Sans"},
        },
        gauge={
            "axis": {
                "range": [min_val, max_val],
                "tickwidth": 1,
                "tickcolor": COLORS["text_muted"],
                "tickfont": {"size": 10, "color": COLORS["text_muted"]},
            },
            "bar": {"color": bar_color, "thickness": 0.75},
            "bgcolor": "#242748",
            "borderwidth": 0,
            "steps": [
                {"range": [min_val, target], "color": "#302650"},
                {"range": [target, max_val], "color": "#3c3f6a"},
            ],
            "threshold": {
                "line": {"color": COLORS["accent"], "width": 3},
                "thickness": 0.8,
                "value": target,
            },
        },
    ))

    fig.update_layout(
        height=height,
        margin=dict(t=50, b=10, l=20, r=20),
        paper_bgcolor=COLORS["bg"],
        font=dict(family="DM Sans, sans-serif"),
    )
    return fig


# ==================== TARGET VS ACTUAL ====================
def target_vs_actual(kpis: List[tuple], height: int = 340) -> go.Figure:
    """Bar chart Target vs Actual."""
    labels = [k[0] for k in kpis]
    actuals = [k[1] for k in kpis]
    targets = [k[2] for k in kpis]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Actual", x=labels, y=actuals,
        marker_color=COLORS["primary"],
        text=[f"<b>{a:,.2f}</b>" for a in actuals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        name="Target", x=labels, y=targets,
        marker_color=COLORS["primary_light"],
        text=[f"{t:,.2f}" for t in targets],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["text_muted"], family="DM Sans"),
        cliponaxis=False,
    ))

    fig = apply_theme(fig, height=height)
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.1)
    return fig


# ==================== COMPARISON BAR ====================
def comparison_bar(labels: List[str], baseline: List[float],
                   simulasi: List[float], height: int = 360,
                   title: str = "", y_title: str = "") -> go.Figure:
    """Bar chart membandingkan baseline vs simulasi."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Baseline",
        x=labels,
        y=baseline,
        marker_color="#6b6f95",
        marker_line_width=0,
        text=[f"<b>{b:,.0f}</b>" for b in baseline],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_muted"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Baseline: %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Simulasi",
        x=labels,
        y=simulasi,
        marker_color=COLORS["primary"],
        marker_line_width=0,
        text=[f"<b>{s:,.0f}</b>" for s in simulasi],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["primary_light"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Simulasi: %{y:,.0f}<extra></extra>",
    ))

    fig = apply_theme(fig, height=height)
    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.1,
        title=dict(
            text=f"<b>{title}</b>" if title else None,
            font=dict(size=14, color=COLORS["text"]),
        ),
        yaxis=dict(
            title=dict(text=f"<b>{y_title}</b>" if y_title else None,
                       font=dict(size=12)),
            tickformat=",.0f",
        ),
    )
    return fig


# ==================== HEATMAP ====================
def heatmap(matrix_data, x_labels: List[str], y_labels: List[str],
            height: int = 380, colorscale: str = "Purples",
            title: str = "") -> go.Figure:
    """Heatmap untuk performance matrix."""
    fig = go.Figure(go.Heatmap(
        z=matrix_data,
        x=x_labels,
        y=y_labels,
        colorscale=colorscale,
        hovertemplate="<b>%{y}</b> · %{x}<br><b>Nilai:</b> %{z:.2f}<extra></extra>",
        colorbar=dict(
            thickness=12,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
            outlinewidth=0,
        ),
    ))

    fig = apply_theme(fig, height=height)
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>" if title else None,
                   font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(showgrid=False, title="", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, title="", tickfont=dict(size=10)),
    )
    return fig


# ==================== RADAR ====================
def radar(categories: List[str], values: List[float],
          targets: Optional[List[float]] = None,
          height: int = 400, title: str = "") -> go.Figure:
    """Radar chart untuk multi-KPI profile."""
    if targets is None:
        targets = [100] * len(categories)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories,
        fill="toself", name="Actual",
        line=dict(color=COLORS["primary"], width=3),
        fillcolor="rgba(164, 137, 255, 0.25)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=targets, theta=categories,
        fill="none", name="Target",
        line=dict(color=COLORS["accent"], width=2, dash="dash"),
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#1a1d3d",
            radialaxis=dict(
                visible=True,
                range=[0, max(max(values), max(targets)) * 1.1],
                gridcolor=COLORS["grid"],
                tickfont=dict(size=9, color=COLORS["text_muted"]),
            ),
            angularaxis=dict(
                gridcolor=COLORS["grid"],
                tickfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
            ),
        ),
        showlegend=True,
        height=height,
        paper_bgcolor=COLORS["bg"],
        margin=dict(t=40, b=40, l=60, r=60),
        title=dict(text=f"<b>{title}</b>" if title else None,
                   font=dict(size=13, color=COLORS["text"])),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center",
                    font=dict(color=COLORS["text_axis"])),
        font=dict(family="DM Sans, sans-serif"),
    )
    return fig


# ==================== CARD WRAPPER ====================
def card_open(title: str, subtitle: str = "") -> None:
    """Buka card wrapper untuk chart — dark theme."""
    import streamlit as st
    st.markdown(f"""
    <div style="background:{COLORS['card_bg']};border:1px solid {COLORS['card_border']};
        border-radius:14px;padding:20px 22px 8px 22px;margin-bottom:16px;
        box-shadow:0 9px 30px rgba(6,9,23,0.13);">
        <div style="font-size:1.05rem;font-weight:700;color:#f5f6ff;
            letter-spacing:-0.3px;margin-bottom:4px;">{title}</div>
        <div style="font-size:0.78rem;color:{COLORS['text_muted']};
            margin-bottom:12px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def card_close() -> None:
    """Tutup card wrapper."""
    import streamlit as st
    st.markdown('<div style="margin-bottom:12px;"></div>', unsafe_allow_html=True)


# ==================== REGISTER TEMPLATE ====================
def register_template() -> None:
    """Daftarkan template default."""
    template = go.layout.Template()
    template.layout = apply_theme(go.Figure()).layout
    pio.templates["decidiq"] = template
    pio.templates.default = "decidiq"