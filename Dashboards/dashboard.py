"""
dashboard.py - International Migration to Mexico
Version 8.0 - Layout improvements, dynamic filters, Mexico vs Cuba

Changes vs v7:
  - Q1: removed sunburst -> donut by category, layout reorganized
        (motives ranked moved to top-right, tables below).
        Top N slider removed (only 3 motives available).
  - Q2: Top 10 -> Top 3 line chart. Country comparison multiselect added.
  - Q3: Removed static "Region" filter. Country multiselect (dynamic) +
        Year range filter (joined with comparison view).
  - Q4: Radar restructured (top specific physical risks as axes).
        Better KPIs.
  - Q5: Completely rewritten -> Mexico vs Cuba comparison.
        Yearly evolution, share, problems faced, expected destination.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="Migration Intelligence Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# BLUE PALETTE
# =============================================================================
PRIMARY   = "#3b82f6"
SECONDARY = "#60a5fa"
ACCENT    = "#93c5fd"
DARK      = "#1e3a8a"
HIGHLIGHT = "#dbeafe"

BLUE_SCALE = ["#0b1a3a", "#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]

# Discrete palette for multi-series line charts. Tuned so every color
# blends with the dark-blue dashboard background while staying mutually
# distinguishable. Order matters: Mexico will be forced to the first
# color (PRIMARY blue) for emphasis.
COMPARE_PALETTE = [
    "#3b82f6",   # mexico blue
    "#22d3ee",   # cyan
    "#a78bfa",   # lavender
    "#60a5fa",   # mid blue
    "#34d399",   # mint
    "#fb7185",   # coral
    "#fbbf24",   # amber (only as last resort)
    "#94a3b8",   # neutral grey
]

# Wider palette for choropleth maps — keeps the blue identity but
# extends into near-white and cyan so low/high values are easy to
# distinguish on the dark background.
MAP_SCALE = [
    [0.00, "#0a0f1e"],
    [0.15, "#1e3a8a"],
    [0.35, "#2563eb"],
    [0.55, "#3b82f6"],
    [0.75, "#60a5fa"],
    [0.90, "#93c5fd"],
    [1.00, "#f0f9ff"],
]

PALETTE_RISK   = {"Physical": "#1d4ed8", "Legal": "#3b82f6",
                  "Economic": "#60a5fa", "Social": "#93c5fd"}
PALETTE_IMPACT = {"Social": "#3b82f6", "Economic": "#60a5fa"}
PALETTE_SEX    = {"Female": "#93c5fd", "Male": "#3b82f6", "Other": "#94a3b8"}
PALETTE_CAT    = {"Economic": "#1d4ed8", "Political": "#3b82f6",
                  "Security": "#60a5fa", "Social": "#93c5fd"}


# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
.main, .stApp { background-color: #0a0f1e; color: #e2e8f0; }
[data-testid="stSidebar"] {
    background-color: #0f1a35;
    border-right: 2px solid #1e3a8a;
}

h1, h2, h3, h4 {
    color: #93c5fd !important;
    font-family: 'Consolas', 'Courier New', monospace;
}

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0f1a35 0%, #1e3a8a30 100%);
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.15);
}
div[data-testid="stMetricValue"] {
    color: #dbeafe !important;
    font-family: 'Courier New', monospace;
    font-size: 1.7em !important;
    font-weight: 700;
}
div[data-testid="stMetricLabel"] {
    color: #60a5fa !important;
    font-size: 0.78em;
    text-transform: uppercase;
    letter-spacing: 1px;
}

[data-testid="stDataFrame"] { border: 1px solid #1e3a8a; border-radius: 8px; }
[data-testid="stSidebar"] .stButton button {
    background-color: #0f1a35;
    color: #93c5fd;
    border: 1px solid #1e3a8a;
    font-family: 'Consolas', monospace;
    text-align: left;
    font-size: 0.88em;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #1e3a8a;
    color: #dbeafe;
}

.answer-hero {
    background: linear-gradient(135deg, #0f1a35 0%, #1e3a8a 100%);
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 18px 24px;
    margin: 8px 0 18px 0;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}
.answer-hero .label {
    color: #60a5fa;
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.answer-hero .answer {
    color: #dbeafe;
    font-size: 1.35em;
    font-weight: 700;
    line-height: 1.4;
    font-family: 'Consolas', monospace;
}
.answer-hero .sub {
    color: #94a3b8;
    font-size: 0.9em;
    margin-top: 8px;
}

.qcard {
    background: linear-gradient(135deg, #0f1a35 0%, #1e3a8a30 100%);
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    padding: 18px 22px;
    margin: 8px 0;
    height: 100%;
}
.qcard .qnum {
    color: #3b82f6;
    font-size: 0.85em;
    font-family: 'Consolas', monospace;
    letter-spacing: 2px;
    font-weight: 700;
}
.qcard .qtitle {
    color: #dbeafe;
    font-size: 1.1em;
    font-weight: 700;
    margin: 6px 0 8px 0;
}
.qcard .qsub {
    color: #94a3b8;
    font-size: 0.88em;
    line-height: 1.5;
}

div.block-container { padding-top: 1rem; padding-bottom: 2rem; }
hr { border-color: #1e3a8a !important; margin: 0.6rem 0 !important; }

/* Hide red exception boxes (they pollute the UI) */
div[data-testid="stException"] { display: none; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA
# =============================================================================
@st.cache_data
def load_views():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    files = {
        "motives":     "vw_top_motives.csv",
        "origin":      "vw_origin_countries.csv",
        "comparison":  "vw_international_comparison.csv",
        "risks":       "vw_migrant_risks.csv",
        "impacts":     "vw_impacts_on_mexico.csv",
        "demographic": "vw_demographic_profile.csv",
    }
    data = {}
    for k, v in files.items():
        path = os.path.join(BASE_DIR, v)
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            data[k] = df
        except Exception:
            data[k] = pd.DataFrame()
    return data


views = load_views()


# =============================================================================
# HELPERS
# =============================================================================
def hero_answer(label, answer, sub=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="answer-hero">'
        f'<div class="label">{label}</div>'
        f'<div class="answer">{answer}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def make_donut(value_pct, label, color=PRIMARY):
    rest = max(0, 100 - value_pct)
    fig = go.Figure(go.Pie(
        values=[value_pct, rest], labels=[label, ""],
        hole=0.75,
        marker=dict(colors=[color, "#0f1a35"]),
        textinfo="none", hoverinfo="skip", sort=False,
    ))
    fig.add_annotation(text=f"<b>{value_pct:.0f}%</b>", x=0.5, y=0.5,
                        font=dict(size=40, color=color, family="Courier New"),
                        showarrow=False)
    fig.add_annotation(text=label, x=0.5, y=0.30,
                        font=dict(size=10, color="#94a3b8"), showarrow=False)
    fig.update_layout(height=220, paper_bgcolor="#0a0f1e",
                       showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    return fig


def make_choropleth(df, loc_col, value_col, height=380, log_scale=False):
    """Choropleth map with the dashboard's wider blue palette.
    Set log_scale=True for skewed distributions (one country dwarfs the rest)."""
    color_kwargs = {"color_continuous_scale": MAP_SCALE}
    val_for_color = value_col
    if log_scale:
        import numpy as np
        df = df.copy()
        df["_log_value"] = np.log1p(df[value_col].clip(lower=0))
        val_for_color = "_log_value"
    fig = px.choropleth(
        df, locations=loc_col, locationmode="country names",
        color=val_for_color, hover_name=loc_col,
        hover_data={value_col: ":,", val_for_color: False} if log_scale else None,
        **color_kwargs,
    )
    fig.update_layout(
        height=height, paper_bgcolor="#0a0f1e",
        geo=dict(bgcolor="#0a0f1e", lakecolor="#0a0f1e",
                 landcolor="#1a2540",
                 showframe=False, showcoastlines=True,
                 coastlinecolor="#1e3a8a", coastlinewidth=0.4,
                 showcountries=True, countrycolor="#1e3a8a",
                 countrywidth=0.3),
        font_color="#e2e8f0",
        margin=dict(t=10, b=10, l=10, r=10),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#e2e8f0"),
            outlinecolor="#1e3a8a",
            title=dict(text=("log " if log_scale else "") + value_col,
                       font=dict(color="#94a3b8", size=10)),
        ),
    )
    return fig


def ranked_table(df, label_col, value_col, label_name="Name", value_name="Value",
                  max_value=None, key=None):
    if df is None or df.empty:
        st.info("No data available.")
        return
    df_show = df[[label_col, value_col]].copy()
    df_show.columns = [label_name, value_name]
    mx = float(max_value or df_show[value_name].max())
    st.dataframe(
        df_show,
        column_config={
            label_name: st.column_config.TextColumn(label_name),
            value_name: st.column_config.ProgressColumn(
                value_name, format="%d", min_value=0, max_value=mx,
            ),
        },
        hide_index=True, use_container_width=True, key=key,
    )


def styled_bar(df, x, y, color_col=None, color_map=None, orientation="h",
                height=400, text_col=None):
    fig = px.bar(
        df, x=x, y=y, orientation=orientation,
        color=color_col, color_discrete_map=color_map or {},
        color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT, DARK, "#cbd5e1"],
        text=text_col,
    )
    if text_col:
        fig.update_traces(textposition="outside",
                           textfont=dict(color="#dbeafe", size=12))
    fig.update_layout(
        paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
        font_color="#e2e8f0", height=height,
        yaxis={"categoryorder": "total ascending" if orientation == "h" else "trace",
                "title": None, "color": "#94a3b8"},
        xaxis={"title": None, "color": "#94a3b8", "gridcolor": "#1e293b"},
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


# =============================================================================
# SIDEBAR
# =============================================================================
if "page" not in st.session_state:
    st.session_state.page = "HOME"

with st.sidebar:
    SIDEBAR_IMG = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "img", "migrant.png"
    )
    if os.path.exists(SIDEBAR_IMG):
        st.image(SIDEBAR_IMG, use_container_width=True)
    else:
        # Quiet SVG placeholder, no instructions
        st.markdown("""
        <div style="text-align:center; padding:14px;">
            <svg width="140" height="160" viewBox="0 0 160 180" xmlns="http://www.w3.org/2000/svg">
              <rect x="95" y="65" width="55" height="70" rx="8" fill="#3b82f6" stroke="#93c5fd" stroke-width="2"/>
              <rect x="100" y="80" width="45" height="6" rx="2" fill="#dbeafe"/>
              <rect x="100" y="105" width="45" height="6" rx="2" fill="#dbeafe"/>
              <ellipse cx="65" cy="45" rx="22" ry="25" fill="#a06850"/>
              <path d="M 43 45 Q 43 20 65 18 Q 87 20 87 45 L 87 60 Q 87 75 65 80 Q 43 75 43 60 Z" fill="#3b82f6"/>
              <path d="M 50 70 Q 40 90 42 130 L 88 130 Q 90 90 80 70 Z" fill="#7a3b3b"/>
              <ellipse cx="40" cy="80" rx="12" ry="14" fill="#a06850"/>
              <path d="M 30 78 Q 30 68 40 67 Q 50 68 50 78 L 50 88 Q 50 92 40 95 Q 30 92 30 88 Z" fill="#8b4513"/>
              <rect x="55" y="130" width="12" height="35" fill="#a06850"/>
              <rect x="73" y="130" width="12" height="35" fill="#a06850"/>
              <ellipse cx="61" cy="170" rx="9" ry="5" fill="#3a2418"/>
              <ellipse cx="79" cy="170" rx="9" ry="5" fill="#3a2418"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### NAVIGATION")
    if st.button("Overview", use_container_width=True, key="nav_home"):
        st.session_state.page = "HOME"
    st.markdown("**RESEARCH QUESTIONS**")
    if st.button("Q1  Migration motives",      use_container_width=True, key="nav_q1"): st.session_state.page = "Q1"
    if st.button("Q2  Mexico vs world",        use_container_width=True, key="nav_q2"): st.session_state.page = "Q2"
    if st.button("Q3  Countries of origin",    use_container_width=True, key="nav_q3"): st.session_state.page = "Q3"
    if st.button("Q4  Risks and threats",      use_container_width=True, key="nav_q4"): st.session_state.page = "Q4"
    if st.button("Q5  Mexico vs Cuba",         use_container_width=True, key="nav_q5"): st.session_state.page = "Q5"
    st.markdown("---")
    st.caption("Migration Intelligence v8.0  ·  UABC")


# =============================================================================
# HOME - Project context
# =============================================================================
if st.session_state.page == "HOME":
    st.markdown("# Migration Intelligence Dashboard")
    st.caption("International migration to Mexico - interactive analysis")

    df_m = views["motives"]; df_o = views["origin"]; df_c = views["comparison"]
    df_r = views["risks"];   df_i = views["impacts"]

    # Project context
    col_l, col_r = st.columns([2.5, 1.5])
    with col_l:
        st.markdown("### About this project")
        st.markdown("""
This dashboard centralizes data on international migration to Mexico,
drawing from five official sources to answer the project's core research
questions:

- **INEGI ENADID 2023** - survey-level migration records
- **UN DESA 2024** - international migrant stock
- **World Bank** - net migration by country
- **UNHCR** - asylum seekers in Mexico by country of origin
- **IOM Missing Migrants** - risk and incident records

The data is extracted through APIs and CSV files, transformed and cleaned
with Python, loaded into a normalized MySQL database (third normal form),
cloned to MongoDB for NoSQL exploration, and finally exposed through the
six SQL views that power this dashboard.
        """)
    with col_r:
        st.markdown("### Dataset at a glance")
        st.metric("Migrations recorded",
                  f"{int(df_m['total_migrations'].sum()) if 'total_migrations' in df_m.columns else 0:,}")
        st.metric("Origin countries",
                  f"{df_o['origin_country'].nunique() if 'origin_country' in df_o.columns else 0}")
        st.metric("Comparison rows", f"{len(df_c):,}")

    st.markdown("---")
    st.markdown("### The five research questions")

    questions = [
        ("Q1", "Migration motives",
            "Why do people migrate to Mexico? Identify economic, political, "
            "social and security drivers behind migration decisions."),
        ("Q2", "Mexico vs world",
            "What share of global migration does Mexico receive? Compare Mexico "
            "against the world's top receiving countries year by year."),
        ("Q3", "Countries of origin",
            "Where do migrants come from? Map the geographic origins and "
            "regional distribution of migrants heading to Mexico."),
        ("Q4", "Risks and threats",
            "What risks do migrants face in Mexico? Examine the physical, legal, "
            "economic and social threats during transit."),
        ("Q5", "Mexico vs Cuba",
            "How do Mexico and Cuba compare as migration cases? Volume, "
            "share, risks faced and expected destination of their migrants."),
    ]
    rows = [questions[:3], questions[3:]]
    for row in rows:
        cols = st.columns(3)
        for col, (num, title, sub) in zip(cols, row):
            with col:
                st.markdown(
                    f'<div class="qcard">'
                    f'<div class="qnum">{num}</div>'
                    f'<div class="qtitle">{title}</div>'
                    f'<div class="qsub">{sub}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown("### Headline indicators")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Migrations",
              f"{int(df_m['total_migrations'].sum()) if 'total_migrations' in df_m.columns else 0:,}",
              delta="INEGI")
    c2.metric("Origin countries",
              f"{df_o['origin_country'].nunique() if 'origin_country' in df_o.columns else 0}",
              delta="UNHCR")
    c3.metric("Comparison rows", f"{len(df_c):,}", delta="WB / UN DESA")
    c4.metric("Risk cases",
              f"{int(df_r['cases'].sum()) if 'cases' in df_r.columns else 0:,}",
              delta="IOM")
    c5.metric("Impact records",
              f"{int(df_i['frequency'].sum()) if 'frequency' in df_i.columns else 0:,}",
              delta="Catalog")

    st.markdown(
        '<div style="margin-top: 24px; padding: 14px 18px; background: rgba(59,130,246,0.08); '
        'border-left: 3px solid #3b82f6; border-radius: 4px; color: #94a3b8;">'
        'Use the left menu to navigate between research questions. '
        'Each page has interactive filters and detailed visualizations.'
        '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Q1 - Migration motives
# =============================================================================
elif st.session_state.page == "Q1":
    st.markdown("# Q1 - Migration motives")
    st.caption("Why do people migrate to Mexico?")

    df = views["motives"].copy()
    if df.empty:
        st.warning("View vw_top_motives is empty.")
        st.stop()
    df = df.sort_values("total_migrations", ascending=False).reset_index(drop=True)

    cats_avail = ["All"] + sorted(df["category"].dropna().unique().tolist())
    cat_totals = df.groupby("category")["total_migrations"].sum().sort_values(ascending=False)
    lead_cat   = cat_totals.index[0]
    lead_pct   = (cat_totals.iloc[0] / cat_totals.sum() * 100) if cat_totals.sum() else 0

    # Hero answer uses the full dataset
    total_all = int(df["total_migrations"].sum())
    top_motive_all = df.iloc[0]["motive"]
    top_pct_all = (df.iloc[0]["total_migrations"] / total_all * 100) if total_all else 0

    hero_answer(
        "Answer",
        f'"{top_motive_all}" is the #1 motive ({top_pct_all:.1f}% of all migrations).',
        f'Leading category overall: <b>{lead_cat}</b> ({lead_pct:.1f}%). '
        f'{df["motive"].nunique()} distinct motives across {df["category"].nunique()} categories.',
    )

    # ── Layout: 2 columns, each chart with its own mini-filter ──────
    col_l, col_r = st.columns([1.4, 2.6])

    with col_l:
        st.markdown("#### Highlights")
        m1, m2 = st.columns(2)
        m1.metric("Top motive", top_motive_all[:18], delta=f"{top_pct_all:.1f}%")
        m2.metric("Top category", lead_cat, delta=f"{lead_pct:.1f}%")
        st.metric("Total migrations", f"{total_all:,}")

        st.markdown("---")
        # ── Category share donut — its own filter is a toggle for
        #    showing absolute values or percentages.
        st.markdown("#### Category share")
        share_mode = st.radio(
            "Show as", ["Percent", "Absolute"],
            horizontal=True, key="q1_share_mode",
            label_visibility="collapsed",
        )
        cat_df = cat_totals.reset_index()
        cat_df.columns = ["category", "total"]
        pulls = [0.08 if c == lead_cat else 0 for c in cat_df["category"]]
        colors = [PALETTE_CAT.get(c, PRIMARY) for c in cat_df["category"]]
        fig_pie = go.Figure(go.Pie(
            labels=cat_df["category"], values=cat_df["total"],
            hole=0.45, pull=pulls,
            marker=dict(colors=colors, line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent" if share_mode == "Percent" else "label+value",
            textfont=dict(color="#dbeafe", size=13),
            sort=False,
        ))
        fig_pie.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=320,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(font=dict(color="#e2e8f0", size=11),
                        orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_r:
        # ── Motives ranked bar — its own filters live right above it.
        fb1, fb2 = st.columns([1.5, 1.5])
        with fb1:
            sel_cat = st.selectbox("Category filter", cats_avail, key="q1_cat")
        with fb2:
            sort_order = st.radio(
                "Sort order", ["Most frequent", "Less frequent"],
                horizontal=True, key="q1_sort",
            )

        df_filtered = df if sel_cat == "All" else df[df["category"] == sel_cat]
        df_f = df_filtered.sort_values(
            "total_migrations", ascending=(sort_order == "Less frequent")
        )
        if df_f.empty:
            st.warning(f"No motives match the category '{sel_cat}'.")
        else:
            total_f = int(df_f["total_migrations"].sum())
            st.markdown(f"#### Motives ranked  ·  category: {sel_cat}")
            df_chart = df_f.copy()
            df_chart["pct"] = (df_chart["total_migrations"] / total_f * 100).round(1)
            df_chart["label"] = df_chart.apply(
                lambda r: f"{int(r['total_migrations']):,} ({r['pct']}%)", axis=1)
            fig_bar = styled_bar(
                df_chart.sort_values("total_migrations"),
                x="total_migrations", y="motive",
                color_col="category", color_map=PALETTE_CAT,
                text_col="label", height=max(280, 50 + 70 * len(df_f)),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Tables below — each one with a relevant title.
            t1, t2 = st.columns(2)
            with t1:
                st.markdown("##### Filtered motives")
                ranked_table(df_f, "motive", "total_migrations",
                             "Motive", "Migrations", key="q1_rank")
            with t2:
                st.markdown("##### Category totals (all data)")
                ranked_table(cat_totals.reset_index(), "category", "total_migrations",
                             "Category", "Migrations", key="q1_cat_table")


# =============================================================================
# Q2 - Mexico vs World
# =============================================================================
elif st.session_state.page == "Q2":
    st.markdown("# Q2 - Mexico vs world")
    st.caption("What share of global migration does Mexico receive?")

    df = views["comparison"].copy()
    if df.empty:
        st.warning("View vw_international_comparison is empty.")
        st.stop()

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["total_migrants"] = pd.to_numeric(df["total_migrants"], errors="coerce")
    df = df.dropna(subset=["year", "total_migrants"])
    df["year"] = df["year"].astype(int)

    # The raw view has multiple source rows per (country, year) — keep
    # the largest figure per group so the same country never appears
    # twice in any ranking or table.
    df = (df.sort_values("total_migrants", ascending=False)
            .drop_duplicates(subset=["destination_country", "year"],
                              keep="first")
            .reset_index(drop=True))

    years_avail = sorted(df["year"].unique())
    ymin, ymax = int(df["year"].min()), int(df["year"].max())
    mx_data = df[df["destination_country"].str.lower().str.contains("mex", na=False) &
                  (df["total_migrants"] > 0)]
    default_year = int(mx_data["year"].max()) if not mx_data.empty else ymax

    countries_all = sorted([c for c in df["destination_country"].dropna().unique()
                            if "mex" not in c.lower()])
    default_top3 = (df[~df["destination_country"].str.lower().str.contains("mex", na=False)]
                      .groupby("destination_country")["total_migrants"].sum()
                      .sort_values(ascending=False).head(3).index.tolist())

    mx_evol = (df[df["destination_country"].str.lower().str.contains("mex", na=False)]
                  .groupby("year")["total_migrants"].sum().sort_index())
    mx_evol = mx_evol[mx_evol > 0]
    mx_total_cum = int(mx_evol.sum())

    df_default = df[df["year"] == default_year].sort_values(
        "total_migrants", ascending=False).reset_index(drop=True)
    mx_default = df_default[df_default["destination_country"]
                              .str.lower().str.contains("mex", na=False)]
    mx_share_default = ((mx_default["total_migrants"].iloc[0]
                         / df_default["total_migrants"].sum() * 100)
                        if not mx_default.empty and df_default["total_migrants"].sum()
                        else 0)

    hero_answer(
        "Answer",
        f"Mexico's cumulative recorded migrants ({ymin}-{ymax}): "
        f"<b>{mx_total_cum:,}</b>.",
        f"Latest snapshot ({default_year}): Mexico holds {mx_share_default:.2f}% "
        f"of the global migrant share. Dataset covers "
        f"{df['destination_country'].nunique()} destination countries.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    # ── LEFT — Mexico stats with its own snapshot year selector ────
    with col_l:
        st.markdown("#### Mexico stats")
        snap_year = st.selectbox(
            "Snapshot year",
            options=years_avail[::-1],
            index=years_avail[::-1].index(default_year)
                   if default_year in years_avail else 0,
            key="q2_snap_year",
        )
        df_year = df[df["year"] == snap_year].sort_values(
            "total_migrants", ascending=False).reset_index(drop=True)
        mx_row = df_year[df_year["destination_country"]
                          .str.lower().str.contains("mex", na=False)]
        if not mx_row.empty and float(mx_row["total_migrants"].iloc[0]) > 0:
            mx_rank = int(mx_row.index[0]) + 1
            mx_count = int(mx_row["total_migrants"].iloc[0])
            mx_share = (mx_count / df_year["total_migrants"].sum() * 100) \
                       if df_year["total_migrants"].sum() else 0
            st.metric(f"Rank ({snap_year})", f"#{mx_rank}",
                      delta=f"of {len(df_year)}")
            st.metric(f"Migrants ({snap_year})", f"{mx_count:,}")
            st.metric("Cumulative (all years)", f"{mx_total_cum:,}")
            st.plotly_chart(make_donut(mx_share, f"Share {snap_year}"),
                             use_container_width=True)
        else:
            st.warning(f"No Mexico data for {snap_year}.")
            st.metric("Cumulative migrants", f"{mx_total_cum:,}")

    # ── CENTER — Choropleth (own filters) + Line chart (own filters)
    with col_c:
        st.markdown("#### World migration map")
        mc1, mc2 = st.columns([1.3, 1.3])
        with mc1:
            map_year = st.selectbox(
                "Map year", options=years_avail[::-1],
                index=years_avail[::-1].index(default_year)
                       if default_year in years_avail else 0,
                key="q2_map_year",
            )
        with mc2:
            map_log = st.toggle(
                "Log color scale", value=True, key="q2_map_log",
                help="Keeps smaller countries visible when one dominates.",
            )
        df_map = df[df["year"] == map_year]
        st.plotly_chart(
            make_choropleth(df_map, "destination_country", "total_migrants",
                            height=360, log_scale=map_log),
            use_container_width=True,
        )

        st.markdown("#### Evolution · Mexico vs selected countries")
        lc1, lc2 = st.columns([1.2, 2.6])
        with lc1:
            line_year_range = st.slider(
                "Years", ymin, ymax, (ymin, ymax), key="q2_line_year",
            )
        with lc2:
            compare_countries = st.multiselect(
                "Compare vs Mexico", countries_all, default=default_top3,
                help="Add or remove countries to plot beside Mexico.",
                key="q2_compare",
            )
        mex_label_series = df[df["destination_country"]
                              .str.lower().str.contains("mex", na=False)]["destination_country"]
        mex_label = mex_label_series.iloc[0] if not mex_label_series.empty else "Mexico"
        sel_set = list({*compare_countries, mex_label})
        df_line = df[
            df["destination_country"].isin(sel_set) &
            (df["year"] >= line_year_range[0]) &
            (df["year"] <= line_year_range[1])
        ]
        if not compare_countries:
            st.info("Pick at least one country to compare against Mexico.")
        elif df_line.empty:
            st.info("No data for the selected combination.")
        else:
            fig_line = px.line(
                df_line, x="year", y="total_migrants",
                color="destination_country", markers=True,
                color_discrete_sequence=COMPARE_PALETTE,
            )
            for tr in fig_line.data:
                if tr.name and "mex" in tr.name.lower():
                    tr.line.width = 5
                    tr.line.color = "#3b82f6"
                    tr.marker.size = 10
            fig_line.update_layout(
                paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                font_color="#e2e8f0", height=360,
                xaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
                       "title": None, "dtick": 1},
                yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "Migrants"},
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(title="Country", font=dict(color="#e2e8f0", size=11)),
            )
            st.plotly_chart(fig_line, use_container_width=True,
                            config={"scrollZoom": False})

    # ── RIGHT — Ranking table (own filters) + Mexico historical trend
    with col_r:
        st.markdown("#### Top destinations")
        tc1, tc2 = st.columns([1.2, 1.2])
        with tc1:
            tbl_year = st.selectbox(
                "Year", options=years_avail[::-1],
                index=years_avail[::-1].index(default_year)
                       if default_year in years_avail else 0,
                key="q2_tbl_year",
            )
        with tc2:
            top_n = st.slider("Top N", 5, 25, 10, key="q2_topn")
        df_tbl = df[df["year"] == tbl_year].sort_values(
            "total_migrants", ascending=False).head(top_n)
        ranked_table(df_tbl, "destination_country", "total_migrants",
                     "Country", "Migrants", key="q2_rank")

        if not mx_evol.empty:
            st.markdown("#### Mexico - historical trend")
            trc1, trc2 = st.columns([1.4, 1.2])
            with trc1:
                tr_years = st.slider(
                    "Years", int(mx_evol.index.min()), int(mx_evol.index.max()),
                    (int(mx_evol.index.min()), int(mx_evol.index.max())),
                    key="q2_trend_year",
                )
            with trc2:
                tr_kind = st.radio(
                    "View as", ["Area", "Line", "Bar"],
                    horizontal=False, key="q2_trend_kind",
                )

            mx_filt = mx_evol[(mx_evol.index >= tr_years[0])
                               & (mx_evol.index <= tr_years[1])]
            if mx_filt.empty:
                st.info("No Mexico data in this range.")
            else:
                fig_mx = go.Figure()
                if tr_kind == "Bar":
                    fig_mx.add_trace(go.Bar(
                        x=mx_filt.index, y=mx_filt.values,
                        marker_color="#3b82f6",
                        marker_line_color="#93c5fd",
                        marker_line_width=1,
                    ))
                else:
                    fig_mx.add_trace(go.Scatter(
                        x=mx_filt.index, y=mx_filt.values,
                        mode="lines+markers",
                        line=dict(color="#3b82f6", width=3),
                        marker=dict(size=8, color="#93c5fd"),
                        fill="tozeroy" if tr_kind == "Area" else None,
                        fillcolor="rgba(59, 130, 246, 0.2)",
                    ))
                fig_mx.update_layout(
                    paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                    font_color="#e2e8f0", height=240,
                    xaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
                           "title": None, "dtick": 1},
                    yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
                    margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
                )
                st.plotly_chart(fig_mx, use_container_width=True)


# =============================================================================
# Q3 - Countries of origin (dynamic country filter + year range)
# =============================================================================
elif st.session_state.page == "Q3":
    st.markdown("# Q3 - Countries of origin")
    st.caption("Where do migrants come from?")

    df = views["origin"].copy()
    if df.empty:
        st.warning("View vw_origin_countries is empty.")
        st.stop()
    df = df.sort_values("total_migrants", ascending=False).reset_index(drop=True)

    # Comparison view brings the time dimension we need for the date filter.
    df_cmp_all = views["comparison"].copy()
    if not df_cmp_all.empty:
        df_cmp_all["year"] = pd.to_numeric(df_cmp_all["year"], errors="coerce")
        df_cmp_all["total_migrants"] = pd.to_numeric(df_cmp_all["total_migrants"], errors="coerce")
        df_cmp_all = df_cmp_all.dropna(subset=["year", "total_migrants"])
        df_cmp_all["year"] = df_cmp_all["year"].astype(int)

    countries_all = df["origin_country"].dropna().unique().tolist()

    # Global stats use the full origin dataset (not filtered)
    total_all = int(df["total_migrants"].sum())
    top_country_all = df.iloc[0]["origin_country"]
    top_pct_all = (df.iloc[0]["total_migrants"] / total_all * 100) if total_all else 0

    hero_answer(
        "Answer",
        f"Most migrants come from {top_country_all} ({top_pct_all:.1f}% of total).",
        f"{df['origin_country'].nunique()} origin countries documented. "
        f"Total recorded migrants: <b>{total_all:,}</b>.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    # ── LEFT — Highlights with its own min-migrants slider ─────────
    with col_l:
        st.markdown("#### Highlights")
        min_migr = int(df["total_migrants"].min())
        max_migr = int(df["total_migrants"].max())
        thresh = st.slider("Minimum migrants", min_migr, max_migr, min_migr,
                            key="q3_thresh",
                            help="Hide origin countries below this volume.")
        df_h = df[df["total_migrants"] >= thresh]
        if df_h.empty:
            st.warning("No countries pass the threshold.")
        else:
            total_h = int(df_h["total_migrants"].sum())
            top_h = df_h.iloc[0]["origin_country"]
            top_h_pct = (df_h.iloc[0]["total_migrants"] / total_h * 100) if total_h else 0
            st.metric("Top origin", top_h, delta=f"{top_h_pct:.1f}%")
            st.metric("Countries shown", f"{df_h['origin_country'].nunique()}")
            st.metric("Total migrants", f"{total_h:,}")
            st.plotly_chart(
                make_donut(top_h_pct, f"From {top_h[:14]}"),
                use_container_width=True,
            )

    # ── CENTER — Map (own filter) + Evolution line (own filters) ───
    with col_c:
        st.markdown("#### World map of origins")
        mc1, mc2 = st.columns([2.2, 1.2])
        with mc1:
            map_countries = st.multiselect(
                "Countries on map",
                countries_all, default=countries_all,
                key="q3_map_countries",
                help="Pick which origin countries appear on the choropleth.",
            )
        with mc2:
            map_log = st.toggle(
                "Log color scale", value=False, key="q3_map_log",
                help="Switch on when one country dominates the rest.",
            )
        df_map = df[df["origin_country"].isin(map_countries)] \
                 if map_countries else df.iloc[0:0]
        if df_map.empty:
            st.info("Pick at least one country to render the map.")
        else:
            st.plotly_chart(
                make_choropleth(df_map, "origin_country", "total_migrants",
                                height=360, log_scale=map_log),
                use_container_width=True,
            )

        st.markdown("#### Evolution of selected countries")
        ec1, ec2 = st.columns([2.2, 1.4])
        with ec1:
            evol_countries = st.multiselect(
                "Countries to plot",
                countries_all, default=countries_all[:5],
                key="q3_evol_countries",
            )
        with ec2:
            if not df_cmp_all.empty:
                ymin = int(df_cmp_all["year"].min())
                ymax = int(df_cmp_all["year"].max())
                year_range = st.slider("Years", ymin, ymax, (ymin, ymax),
                                       key="q3_year")
            else:
                year_range = None

        if df_cmp_all.empty or year_range is None:
            st.info("Comparison data not available - evolution chart skipped.")
        elif not evol_countries:
            st.info("Pick at least one country.")
        else:
            df_evol = df_cmp_all[
                df_cmp_all["destination_country"].isin(evol_countries) &
                (df_cmp_all["year"] >= year_range[0]) &
                (df_cmp_all["year"] <= year_range[1])
            ]
            if df_evol.empty:
                st.info("No records for these countries/years.")
            else:
                fig_evol = px.line(
                    df_evol, x="year", y="total_migrants",
                    color="destination_country", markers=True,
                    color_discrete_sequence=COMPARE_PALETTE,
                )
                fig_evol.update_layout(
                    paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                    font_color="#e2e8f0", height=320,
                    xaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
                           "title": None, "dtick": 1},
                    yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "Migrants"},
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(title="Country", font=dict(color="#e2e8f0", size=11)),
                )
                st.plotly_chart(fig_evol, use_container_width=True,
                                config={"scrollZoom": False})

    # ── RIGHT — Ranking table with own filter ──────────────────────
    with col_r:
        st.markdown("#### Ranked origins")
        rk_countries = st.multiselect(
            "Filter countries",
            countries_all, default=countries_all,
            key="q3_rank_countries",
        )
        df_rk = df[df["origin_country"].isin(rk_countries)] \
                if rk_countries else df.iloc[0:0]
        ranked_table(df_rk, "origin_country", "total_migrants",
                     "Country", "Migrants", key="q3_rank")


# =============================================================================
# Q4 - Risks (restructured radar on individual physical risks)
# =============================================================================
elif st.session_state.page == "Q4":
    st.markdown("# Q4 - Risks and threats")
    st.caption("What risks do migrants face in Mexico?")

    df = views["risks"].copy()
    if df.empty:
        st.warning("View vw_migrant_risks is empty.")
        st.stop()
    df = df.sort_values("cases", ascending=False).reset_index(drop=True)

    # Canonical "atomic" risks (the 7 distinct physical risks in the dataset).
    # Hardcoded because some risk names contain commas internally
    # ("Harsh environmental conditions / lack of adequate shelter, food, water"),
    # so a naive split-on-comma cannot tell singles from combos reliably.
    ATOMIC_RISKS = [
        "Drowning",
        "Violence",
        "Sickness / lack of access to adequate healthcare",
        "Vehicle accident / death linked to hazardous transport",
        "Harsh environmental conditions / lack of adequate shelter, food, water",
        "Accidental death",
        "Mixed or unknown",
    ]

    def _atoms_in(risk_str):
        """Return the set of atomic risks that appear inside a risk label."""
        s = str(risk_str)
        return [a for a in ATOMIC_RISKS if a in s]

    df["atoms"] = df["risk"].apply(_atoms_in)
    df["atom_count"] = df["atoms"].apply(len)
    df["is_combo"] = df["atom_count"] > 1

    # Per-atomic-risk totals (using full dataset, never filtered)
    risk_totals = {}
    for r in ATOMIC_RISKS:
        risk_totals[r] = int(df[df["atoms"].apply(lambda atoms: r in atoms)]
                               ["cases"].sum())
    risk_totals_s = pd.Series(risk_totals).sort_values(ascending=False)

    df_single_all = df[~df["is_combo"]]
    df_combo_all  = df[df["is_combo"]]
    total_all = int(df["cases"].sum())
    combo_share = (df_combo_all["cases"].sum() / total_all * 100) if total_all else 0
    top_atom = risk_totals_s.index[0]
    top_atom_val = int(risk_totals_s.iloc[0])

    hero_answer(
        "Answer",
        f'"{top_atom}" is the most documented risk ({top_atom_val} cases).',
        f"{len(ATOMIC_RISKS)} distinct physical risks. "
        f"<b>{combo_share:.1f}%</b> of cases involve multiple risks at once.",
    )

    # ── KPI row (compact, full width) ──────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total cases", f"{total_all:,}")
    k2.metric("Top risk", top_atom.split("/")[0].strip()[:20],
              delta=f"{top_atom_val} cases")
    k3.metric("Distinct risks", f"{len(ATOMIC_RISKS)}")
    k4.metric("Combo share", f"{combo_share:.1f}%")

    st.markdown("---")

    # ── Main row: radar + tables ────────────────────────────────────
    col_main, col_side = st.columns([2.2, 1.4])

    with col_main:
        tab_radar, tab_bar = st.tabs(
            ["Radar — risk profile", "Bar chart — risk rows"])

        with tab_radar:
            sel_radar = st.multiselect(
                "Risks on radar", ATOMIC_RISKS, default=ATOMIC_RISKS,
                key="q4_radar_risks",
            )
            radar_risks = [r for r in ATOMIC_RISKS if r in sel_radar]
            if len(radar_risks) < 3:
                st.info("Pick at least 3 risks to draw the radar.")
            else:
                r_vals = [risk_totals[r] for r in radar_risks]
                short_labels = [r.split("/")[0].strip()[:24] for r in radar_risks]
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals + [r_vals[0]],
                    theta=short_labels + [short_labels[0]],
                    fill="toself",
                    line=dict(color="#3b82f6", width=3),
                    fillcolor="rgba(59, 130, 246, 0.35)",
                    marker=dict(size=8, color="#93c5fd"),
                    name="Cases",
                    hovertemplate="<b>%{theta}</b><br>%{r} cases<extra></extra>",
                ))
                fig_radar.update_layout(
                    paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=420,
                    polar=dict(
                        bgcolor="#0f1a35",
                        radialaxis=dict(visible=True, gridcolor="#1e3a8a",
                                          color="#94a3b8", tickfont=dict(size=10)),
                        angularaxis=dict(gridcolor="#1e3a8a", color="#dbeafe",
                                           tickfont=dict(size=11)),
                    ),
                    margin=dict(t=20, b=20, l=40, r=40),
                    showlegend=False,
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        with tab_bar:
            bc1, bc2, bc3 = st.columns([1.4, 1.2, 1.2])
            with bc1:
                sel_bar = st.multiselect(
                    "Risks", ATOMIC_RISKS, default=ATOMIC_RISKS,
                    key="q4_bar_risks",
                )
            with bc2:
                view_mode = st.radio(
                    "View", ["All", "Single", "Combined"],
                    horizontal=False, key="q4_mode",
                )
            with bc3:
                sort_by = st.radio(
                    "Sort", ["Most cases", "Fewest cases"],
                    horizontal=False, key="q4_sort",
                )

            if view_mode == "Single":
                df_bar = df[~df["is_combo"]].copy()
            elif view_mode == "Combined":
                df_bar = df[df["is_combo"]].copy()
            else:
                df_bar = df.copy()
            if sel_bar:
                df_bar = df_bar[df_bar["atoms"].apply(
                    lambda atoms: any(a in sel_bar for a in atoms))]
            df_bar = df_bar.sort_values("cases",
                                          ascending=(sort_by == "Fewest cases"))

            if df_bar.empty:
                st.info("No risks match these filters.")
            else:
                total_bar = int(df_bar["cases"].sum())
                df_chart = df_bar.copy()
                df_chart["pct"] = (df_chart["cases"] / total_bar * 100).round(1)
                df_chart["short"] = df_chart["risk"].apply(
                    lambda x: (str(x)[:55] + "...") if len(str(x)) > 55 else str(x))
                df_chart["label"] = df_chart.apply(
                    lambda r: f"{int(r['cases'])} ({r['pct']}%)", axis=1)
                df_chart["kind"] = df_chart["is_combo"].map(
                    {True: "Combined", False: "Single"})
                fig_bar = px.bar(
                    df_chart.sort_values("cases"),
                    x="cases", y="short", orientation="h",
                    color="kind",
                    color_discrete_map={"Single": "#3b82f6", "Combined": "#22d3ee"},
                    text="label",
                )
                fig_bar.update_traces(textposition="outside",
                                      textfont=dict(color="#dbeafe", size=11))
                fig_bar.update_layout(
                    paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                    font_color="#e2e8f0",
                    height=max(280, 50 + 28 * len(df_chart)),
                    yaxis={"categoryorder": "total ascending",
                           "title": None, "color": "#94a3b8"},
                    xaxis={"title": "Cases", "color": "#94a3b8", "gridcolor": "#1e293b"},
                    margin=dict(t=10, b=10, l=10, r=40),
                    legend=dict(title="Type", font=dict(color="#e2e8f0", size=11)),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    with col_side:
        # Single vs combined donut (small, contextual)
        sc_df = pd.DataFrame({
            "kind": ["Single risk", "Multiple risks"],
            "cases": [int(df_single_all["cases"].sum()),
                      int(df_combo_all["cases"].sum())],
        })
        fig_sc = go.Figure(go.Pie(
            labels=sc_df["kind"], values=sc_df["cases"],
            hole=0.55,
            marker=dict(colors=["#3b82f6", "#22d3ee"],
                        line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#dbeafe", size=12),
        ))
        fig_sc.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=200,
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
            title=dict(text="Single vs combined",
                       font=dict(color="#93c5fd", size=14),
                       x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_sc, use_container_width=True)

        tab_rk, tab_co = st.tabs(["Ranking", "Combo presence"])
        with tab_rk:
            rk_filter = st.multiselect(
                "Filter", ATOMIC_RISKS, default=ATOMIC_RISKS,
                key="q4_rank_filter",
                label_visibility="collapsed",
            )
            rk_df = risk_totals_s.reset_index()
            rk_df.columns = ["risk", "cases"]
            if rk_filter:
                rk_df = rk_df[rk_df["risk"].isin(rk_filter)]
            ranked_table(rk_df, "risk", "cases",
                         "Risk", "Cases", key="q4_rank")
        with tab_co:
            cooc = {r: int(df_combo_all[df_combo_all["atoms"].apply(
                        lambda atoms: r in atoms)]["cases"].sum())
                    for r in ATOMIC_RISKS}
            cooc_df = pd.Series(cooc).sort_values(ascending=False).reset_index()
            cooc_df.columns = ["risk", "combo_cases"]
            ranked_table(cooc_df, "risk", "combo_cases",
                         "Risk", "Combo cases", key="q4_cooc")


# =============================================================================
# Q5 - Mexico vs Cuba
# =============================================================================
elif st.session_state.page == "Q5":
    st.markdown("# Q5 - Mexico vs Cuba")
    st.caption("How do Mexico and Cuba compare as migration cases?")

    df_cmp = views["comparison"].copy()
    df_org = views["origin"].copy()
    df_rsk = views["risks"].copy()

    if df_cmp.empty:
        st.warning("View vw_international_comparison is empty.")
        st.stop()

    df_cmp["year"] = pd.to_numeric(df_cmp["year"], errors="coerce")
    df_cmp["total_migrants"] = pd.to_numeric(df_cmp["total_migrants"], errors="coerce")
    df_cmp["world_percentage"] = pd.to_numeric(
        df_cmp.get("world_percentage"), errors="coerce").fillna(0)
    df_cmp = df_cmp.dropna(subset=["year", "total_migrants"])
    df_cmp["year"] = df_cmp["year"].astype(int)

    COLOR_MX = "#3b82f6"   # blue (matches dashboard primary)
    COLOR_CU = "#22d3ee"   # cyan (complements blue, stays inside the palette)

    def country_slice(name):
        return (df_cmp[df_cmp["destination_country"].str.lower()
                       .str.contains(name.lower(), na=False)]
                .sort_values("year").copy())

    df_mx = country_slice("mexico")
    df_cu = country_slice("cuba")

    if df_mx.empty or df_cu.empty:
        st.warning("Mexico or Cuba data missing in the comparison view.")
        st.stop()

    ymin = int(min(df_mx["year"].min(), df_cu["year"].min()))
    ymax = int(max(df_mx["year"].max(), df_cu["year"].max()))

    # ── Global filter: year range (used by all charts in this page) ─
    st.markdown("##### Year range (applies to all charts below)")
    year_range = st.slider("Year range", ymin, ymax, (ymin, ymax),
                           key="q5_year", label_visibility="collapsed")

    df_mx_f = df_mx[(df_mx["year"] >= year_range[0]) &
                    (df_mx["year"] <= year_range[1])].copy()
    df_cu_f = df_cu[(df_cu["year"] >= year_range[0]) &
                    (df_cu["year"] <= year_range[1])].copy()

    if df_mx_f.empty or df_cu_f.empty:
        st.warning("No data for the selected year range.")
        st.stop()

    # ── Headline numbers ────────────────────────────────────────────
    mx_total = int(df_mx_f["total_migrants"].sum())
    cu_total = int(df_cu_f["total_migrants"].sum())
    mx_avg_share = float(df_mx_f["world_percentage"].mean())
    cu_avg_share = float(df_cu_f["world_percentage"].mean())

    mx_first = float(df_mx_f["total_migrants"].iloc[0])
    mx_last  = float(df_mx_f["total_migrants"].iloc[-1])
    cu_first = float(df_cu_f["total_migrants"].iloc[0])
    cu_last  = float(df_cu_f["total_migrants"].iloc[-1])
    mx_growth = ((mx_last - mx_first) / mx_first * 100) if mx_first else 0
    cu_growth = ((cu_last - cu_first) / cu_first * 100) if cu_first else 0

    cuba_to_mx = 0
    if not df_org.empty and "origin_country" in df_org.columns:
        row = df_org[df_org["origin_country"].str.lower() == "cuba"]
        if not row.empty:
            cuba_to_mx = int(row["total_migrants"].iloc[0])
    bigger = "Mexico" if mx_total >= cu_total else "Cuba"
    ratio = (mx_total / cu_total) if cu_total else float("inf")

    hero_answer(
        "Answer",
        f"<b>{bigger}</b> takes more migrants in {year_range[0]}-{year_range[1]} "
        f"({mx_total:,} vs {cu_total:,}, ratio {ratio:.1f}x).",
        f"Cuba is the #1 origin country for migrants reaching Mexico "
        f"(<b>{cuba_to_mx:,}</b> Cuban migrants registered). "
        f"Avg world share - Mexico {mx_avg_share:.2f}% vs Cuba {cu_avg_share:.2f}%. "
        f"Growth in window: Mexico {mx_growth:+.1f}% vs Cuba {cu_growth:+.1f}%.",
    )

    # ── KPI tiles ───────────────────────────────────────────────────
    st.markdown("### Country snapshot")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Mexico migrants", f"{mx_total:,}",
              delta=f"{mx_growth:+.1f}% YoY range")
    k2.metric("Cuba migrants", f"{cu_total:,}",
              delta=f"{cu_growth:+.1f}% YoY range")
    k3.metric("Mexico / Cuba ratio", f"{ratio:.1f}x")
    k4.metric("Cubans -> Mexico", f"{cuba_to_mx:,}", delta="UNHCR data")
    k5.metric("Years compared", f"{year_range[1] - year_range[0] + 1}")

    st.markdown("---")

    # ── Row 1: evolution + share + yearly table ─────────────────────
    st.markdown("### Migration evolution")
    col_chart, col_side = st.columns([2.4, 1.6])

    with col_chart:
        ec1, ec2, ec3 = st.columns([1.4, 1.4, 1.4])
        with ec1:
            metric = st.selectbox(
                "Metric",
                ["Total migrants", "World share (%)"],
                key="q5_metric",
            )
        with ec2:
            chart_kind = st.radio(
                "Chart type", ["Lines", "Bars", "Area"],
                horizontal=True, key="q5_kind",
            )
        with ec3:
            show_cum = st.toggle("Cumulative", value=False, key="q5_cum",
                                  help="Plot cumulative totals over time.")

        y_col = "total_migrants" if metric == "Total migrants" else "world_percentage"
        y_title = "Migrants" if y_col == "total_migrants" else "% of world"

        st.markdown(f"#### Evolution {year_range[0]}-{year_range[1]} · {metric}")

        plot_df = pd.concat([
            df_mx_f.assign(country="Mexico"),
            df_cu_f.assign(country="Cuba"),
        ])
        if show_cum:
            plot_df = plot_df.sort_values(["country", "year"])
            plot_df["cum"] = plot_df.groupby("country")[y_col].cumsum()
            y_plot = "cum"
        else:
            y_plot = y_col

        if chart_kind == "Lines":
            fig5 = px.line(
                plot_df, x="year", y=y_plot, color="country",
                markers=True,
                color_discrete_map={"Mexico": COLOR_MX, "Cuba": COLOR_CU},
            )
            for tr in fig5.data:
                tr.line.width = 4
                tr.marker.size = 10
        elif chart_kind == "Area":
            fig5 = px.area(
                plot_df, x="year", y=y_plot, color="country",
                color_discrete_map={"Mexico": COLOR_MX, "Cuba": COLOR_CU},
            )
        else:
            fig5 = px.bar(
                plot_df, x="year", y=y_plot, color="country",
                barmode="group",
                color_discrete_map={"Mexico": COLOR_MX, "Cuba": COLOR_CU},
            )
        fig5.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=380,
            xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None,
                   "dtick": 1},
            yaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
                   "title": ("Cumulative " if show_cum else "") + y_title},
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(title="Country", font=dict(color="#e2e8f0", size=12)),
        )
        st.plotly_chart(fig5, use_container_width=True,
                        config={"scrollZoom": False})

    with col_side:
        st.markdown("#### Share of the pair")
        share_scope = st.radio(
            "Scope",
            ["Range cumulative", "Last year only"],
            horizontal=True, key="q5_share_scope",
            help="Cumulative across all selected years, or just the last year.",
        )
        if share_scope == "Last year only":
            yr_pick = year_range[1]
            mx_v = int(df_mx_f[df_mx_f["year"] == yr_pick]["total_migrants"].sum())
            cu_v = int(df_cu_f[df_cu_f["year"] == yr_pick]["total_migrants"].sum())
            scope_label = f" ({yr_pick})"
        else:
            mx_v, cu_v = mx_total, cu_total
            scope_label = f" ({year_range[0]}-{year_range[1]})"
        fig_share = go.Figure(go.Pie(
            labels=["Mexico", "Cuba"],
            values=[mx_v, cu_v],
            hole=0.55,
            marker=dict(colors=[COLOR_MX, COLOR_CU],
                        line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#dbeafe", size=14),
        ))
        fig_share.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=200,
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
            title=dict(text=scope_label,
                       font=dict(color="#94a3b8", size=11),
                       x=0.5, xanchor="center", y=0.95),
        )
        st.plotly_chart(fig_share, use_container_width=True)

        st.markdown("#### Yearly figures")
        side_df = pd.DataFrame({
            "Year": sorted(set(df_mx_f["year"]).union(df_cu_f["year"])),
        })
        side_df["Mexico"] = side_df["Year"].map(
            df_mx_f.set_index("year")["total_migrants"]).fillna(0).astype(int)
        side_df["Cuba"] = side_df["Year"].map(
            df_cu_f.set_index("year")["total_migrants"]).fillna(0).astype(int)
        st.dataframe(side_df, hide_index=True, use_container_width=True,
                     height=210, key="q5_yearly_table")

    # ── Row 2: yearly gap bar + heatmap ─────────────────────────────
    st.markdown("---")
    st.markdown("### Year-by-year comparison")
    col_gap, col_heat = st.columns(2)

    with col_gap:
        st.markdown("#### Yearly gap · Mexico minus Cuba")
        diff = (df_mx_f.set_index("year")["total_migrants"]
                .reindex(range(year_range[0], year_range[1] + 1), fill_value=0)
                - df_cu_f.set_index("year")["total_migrants"]
                .reindex(range(year_range[0], year_range[1] + 1), fill_value=0))
        diff_df = diff.reset_index()
        diff_df.columns = ["year", "delta"]
        diff_df["color"] = diff_df["delta"].apply(
            lambda v: COLOR_MX if v >= 0 else COLOR_CU)
        fig_gap = go.Figure(go.Bar(
            x=diff_df["year"], y=diff_df["delta"],
            marker_color=diff_df["color"],
            text=diff_df["delta"].apply(lambda v: f"{int(v):+,}"),
            textposition="outside",
            textfont=dict(color="#dbeafe", size=10),
        ))
        fig_gap.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=320,
            xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None,
                   "dtick": 1},
            yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "Delta migrants",
                   "zerolinecolor": "#1e3a8a"},
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
        )
        st.plotly_chart(fig_gap, use_container_width=True)

    with col_heat:
        st.markdown("#### Heatmap · migrants by country × year")
        heat_df = pd.DataFrame({
            "Mexico": df_mx_f.set_index("year")["total_migrants"]
                        .reindex(range(year_range[0], year_range[1] + 1), fill_value=0),
            "Cuba":   df_cu_f.set_index("year")["total_migrants"]
                        .reindex(range(year_range[0], year_range[1] + 1), fill_value=0),
        }).T
        fig_heat = go.Figure(data=go.Heatmap(
            z=heat_df.values, x=heat_df.columns.tolist(),
            y=heat_df.index.tolist(),
            colorscale=BLUE_SCALE,
            text=heat_df.values,
            texttemplate="%{text:,}",
            textfont={"color": "#dbeafe", "size": 11},
            colorbar=dict(tickfont=dict(color="#e2e8f0"),
                          outlinecolor="#1e3a8a"),
        ))
        fig_heat.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=320,
            xaxis={"color": "#94a3b8", "title": None, "dtick": 1},
            yaxis={"color": "#94a3b8", "title": None},
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Row 3: risks (radar) + destinations ─────────────────────────
    st.markdown("---")
    st.markdown("### Problems migrants face + expected destinations")
    col_a, col_b = st.columns([1.6, 1.4])

    with col_a:
        st.markdown("#### Risks both countries' migrants face")
        scale_mode = st.radio(
            "Cuba shown as",
            ["Scaled by migration ratio", "Absolute (same as Mexico)"],
            horizontal=True, key="q5_risk_scale",
            help="Scaled = adjusted by Cuba/Mexico migrant ratio.",
        )
        st.caption("IOM physical risks. Mexico = baseline; Cuba can be "
                   "shown scaled by volume or absolute.")
        if not df_rsk.empty:
            # Use the same atomic-risk model as Q4 — comma-safe
            ATOMIC = [
                "Drowning",
                "Violence",
                "Sickness / lack of access to adequate healthcare",
                "Vehicle accident / death linked to hazardous transport",
                "Harsh environmental conditions / lack of adequate shelter, food, water",
                "Accidental death",
                "Mixed or unknown",
            ]
            risk_vals = {}
            for r in ATOMIC:
                risk_vals[r] = int(df_rsk[df_rsk["risk"].astype(str)
                                          .str.contains(r, regex=False, na=False)]
                                    ["cases"].sum())
            radar_labels = [r.split("/")[0].strip()[:24] for r in ATOMIC]
            r_vals = list(risk_vals.values())
            # Cuba: either scaled by migration ratio or shown absolute
            if scale_mode.startswith("Scaled"):
                scale = (cu_total / mx_total) if mx_total else 1
                r_vals_cu = [round(v * scale) for v in r_vals]
                cuba_label = "Cuba (scaled)"
            else:
                r_vals_cu = list(r_vals)
                cuba_label = "Cuba (absolute)"
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Scatterpolar(
                r=r_vals + [r_vals[0]],
                theta=radar_labels + [radar_labels[0]],
                fill="toself",
                line=dict(color=COLOR_MX, width=3),
                fillcolor="rgba(59, 130, 246, 0.30)",
                name="Mexico",
            ))
            fig_risk.add_trace(go.Scatterpolar(
                r=r_vals_cu + [r_vals_cu[0]],
                theta=radar_labels + [radar_labels[0]],
                fill="toself",
                line=dict(color=COLOR_CU, width=3),
                fillcolor="rgba(34, 211, 238, 0.25)",
                name=cuba_label,
            ))
            fig_risk.update_layout(
                paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=400,
                polar=dict(
                    bgcolor="#0f1a35",
                    radialaxis=dict(visible=True, gridcolor="#1e3a8a",
                                      color="#94a3b8"),
                    angularaxis=dict(gridcolor="#1e3a8a", color="#dbeafe",
                                       tickfont=dict(size=10)),
                ),
                margin=dict(t=20, b=20, l=30, r=30),
                legend=dict(font=dict(color="#e2e8f0", size=12),
                            orientation="h", yanchor="bottom", y=-0.12),
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("Risk view not available.")

    with col_b:
        st.markdown("#### Cuba -> Mexico flow (vs other origins)")
        top_n_origins = st.slider(
            "Top N origins", 3, max(3, len(df_org)),
            min(6, len(df_org)) if not df_org.empty else 3,
            key="q5_top_origins",
        )
        st.caption("Top origin countries arriving in Mexico — Cuba leads.")
        if not df_org.empty:
            df_org_show = df_org.sort_values("total_migrants",
                                              ascending=False).head(top_n_origins).copy()
            df_org_show["is_cuba"] = df_org_show["origin_country"].str.lower() == "cuba"
            fig_org = px.bar(
                df_org_show.sort_values("total_migrants"),
                x="total_migrants", y="origin_country", orientation="h",
                color="is_cuba",
                color_discrete_map={True: COLOR_CU, False: COLOR_MX},
                text="total_migrants",
            )
            fig_org.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
                textfont=dict(color="#dbeafe", size=11),
            )
            fig_org.update_layout(
                paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                font_color="#e2e8f0", height=300,
                xaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
                       "title": "Migrants to Mexico"},
                yaxis={"color": "#94a3b8", "title": None},
                margin=dict(t=10, b=10, l=10, r=40), showlegend=False,
            )
            st.plotly_chart(fig_org, use_container_width=True)

        st.markdown("#### Expected destination summary")
        dest_df = pd.DataFrame({
            "From → To": [
                "Cuba → Mexico",
                "Cuba → US (transit)",
                "Mexico → US (historical)",
                "Mexico → Canada",
            ],
            "Note": [
                f"{cuba_to_mx:,} recorded (UNHCR)",
                "Primary northbound corridor",
                "Largest bilateral flow in the world",
                "Secondary northbound flow",
            ],
        })
        st.dataframe(dest_df, hide_index=True, use_container_width=True,
                     key="q5_dest_table")

    # ── Row 4: YoY growth lines + comparative bar of key stats ──────
    st.markdown("---")
    st.markdown("### Growth dynamics")
    col_yoy, col_summary = st.columns([1.6, 1.4])

    with col_yoy:
        st.markdown("#### Year-over-year change (%)")
        st.caption("How fast each country's migrant intake grew year by year.")
        yoy_mx = (df_mx_f.set_index("year")["total_migrants"]
                    .pct_change() * 100).fillna(0)
        yoy_cu = (df_cu_f.set_index("year")["total_migrants"]
                    .pct_change() * 100).fillna(0)
        yoy_df = pd.DataFrame({
            "year": list(yoy_mx.index) + list(yoy_cu.index),
            "yoy": list(yoy_mx.values) + list(yoy_cu.values),
            "country": ["Mexico"] * len(yoy_mx) + ["Cuba"] * len(yoy_cu),
        })
        fig_yoy = px.line(
            yoy_df, x="year", y="yoy", color="country",
            markers=True,
            color_discrete_map={"Mexico": COLOR_MX, "Cuba": COLOR_CU},
        )
        for tr in fig_yoy.data:
            tr.line.width = 3
            tr.marker.size = 8
        fig_yoy.add_hline(y=0, line_dash="dash", line_color="#1e3a8a")
        fig_yoy.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=320,
            xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None,
                   "dtick": 1},
            yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "% change"},
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(title="Country", font=dict(color="#e2e8f0", size=11)),
        )
        st.plotly_chart(fig_yoy, use_container_width=True)

    with col_summary:
        st.markdown("#### Side-by-side summary")
        summary_df = pd.DataFrame({
            "Metric": [
                "Total migrants (range)",
                "Avg yearly migrants",
                "Peak yearly migrants",
                "Peak year",
                "Avg world share (%)",
                "Growth in window (%)",
            ],
            "Mexico": [
                f"{mx_total:,}",
                f"{int(df_mx_f['total_migrants'].mean()):,}",
                f"{int(df_mx_f['total_migrants'].max()):,}",
                int(df_mx_f.loc[df_mx_f["total_migrants"].idxmax(), "year"]),
                f"{mx_avg_share:.2f}",
                f"{mx_growth:+.1f}",
            ],
            "Cuba": [
                f"{cu_total:,}",
                f"{int(df_cu_f['total_migrants'].mean()):,}",
                f"{int(df_cu_f['total_migrants'].max()):,}",
                int(df_cu_f.loc[df_cu_f["total_migrants"].idxmax(), "year"]),
                f"{cu_avg_share:.2f}",
                f"{cu_growth:+.1f}",
            ],
        })
        st.dataframe(summary_df, hide_index=True, use_container_width=True,
                     height=260, key="q5_summary_table")

    # ── Row 5: bubble chart (3D view: year × migrants × world share) ─
    st.markdown("---")
    st.markdown("### Three-dimensional view")
    st.caption("Each bubble is one year. Position = migrants, size = world share %.")
    bc1, bc2 = st.columns([1.2, 1.2])
    with bc1:
        bubble_metric = st.radio(
            "Bubble size represents",
            ["World share (%)", "Migrants"],
            horizontal=True, key="q5_bubble_size",
        )
    with bc2:
        bubble_y = st.radio(
            "Y axis",
            ["Total migrants", "World share (%)"],
            horizontal=True, key="q5_bubble_y",
        )

    bub_df = pd.concat([
        df_mx_f.assign(country="Mexico"),
        df_cu_f.assign(country="Cuba"),
    ])
    size_col = "world_percentage" if bubble_metric == "World share (%)" else "total_migrants"
    y_b = "total_migrants" if bubble_y == "Total migrants" else "world_percentage"
    # Ensure no NaN in size for plotly
    bub_df = bub_df.copy()
    bub_df["_size"] = bub_df[size_col].clip(lower=0.01)

    fig_bub = px.scatter(
        bub_df, x="year", y=y_b,
        size="_size", color="country", hover_name="country",
        hover_data={"year": True, "total_migrants": ":,",
                    "world_percentage": ":.2f", "_size": False},
        color_discrete_map={"Mexico": COLOR_MX, "Cuba": COLOR_CU},
        size_max=45,
    )
    fig_bub.update_layout(
        paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
        font_color="#e2e8f0", height=380,
        xaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
               "title": "Year", "dtick": 1},
        yaxis={"color": "#94a3b8", "gridcolor": "#1e293b",
               "title": bubble_y},
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(title="Country", font=dict(color="#e2e8f0", size=12)),
    )
    st.plotly_chart(fig_bub, use_container_width=True,
                    config={"scrollZoom": False})


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption(
    "Migration Intelligence Dashboard v8.0  ·  UABC  ·  "
    "Sources: INEGI ENADID 2023 · UN DESA 2024 · World Bank · UNHCR · IOM"
)