"""
dashboard.py - International Migration to Mexico
Version 7.0 - No emojis, context home, varied charts, more filters

Changes vs v6:
  - No emojis anywhere (clean text titles)
  - HOME page restored with project context + question explanations
  - Q1 rendering fixed (removed problematic HTML wrapper)
  - Q3: scatter chart added, more filter interaction
  - Q4: pie chart and radar variety
  - Q5: more filters
  - Sidebar fallback message removed
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


def make_choropleth(df, loc_col, value_col, height=380):
    fig = px.choropleth(
        df, locations=loc_col, locationmode="country names",
        color=value_col, hover_name=loc_col,
        color_continuous_scale=BLUE_SCALE,
    )
    fig.update_layout(
        height=height, paper_bgcolor="#0a0f1e",
        geo=dict(bgcolor="#0a0f1e", lakecolor="#0a0f1e",
                 landcolor="#0f1a35",
                 showframe=False, showcoastlines=False),
        font_color="#e2e8f0",
        margin=dict(t=10, b=10, l=10, r=10),
        coloraxis_colorbar=dict(tickfont=dict(color="#e2e8f0"),
                                  outlinecolor="#1e3a8a"),
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
    if st.button("Q5  Impact analysis",        use_container_width=True, key="nav_q5"): st.session_state.page = "Q5"
    st.markdown("---")
    st.caption("Migration Intelligence v7.0  ·  UABC")


# =============================================================================
# HOME — Project context
# =============================================================================
if st.session_state.page == "HOME":
    st.markdown("# Migration Intelligence Dashboard")
    st.caption("International migration to Mexico — interactive analysis")

    df_m = views["motives"]; df_o = views["origin"]; df_c = views["comparison"]
    df_r = views["risks"];   df_i = views["impacts"]

    # ── Project context ─────────────────────────────────────────────
    col_l, col_r = st.columns([2.5, 1.5])
    with col_l:
        st.markdown("### About this project")
        st.markdown("""
This dashboard centralizes data on international migration to Mexico,
drawing from five official sources to answer the project's core research
questions:

- **INEGI ENADID 2023** — survey-level migration records
- **UN DESA 2024** — international migrant stock
- **World Bank** — net migration by country
- **UNHCR** — asylum seekers in Mexico by country of origin
- **IOM Missing Migrants** — risk and incident records

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
        ("Q5", "Impact analysis",
            "What is the social and economic impact on Mexico? Measure how "
            "migration shapes Mexico's healthcare, labor, culture and economy."),
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
    c3.metric("Comparison rows", f"{len(df_c):,}", delta="WB · UN DESA")
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
    st.markdown("# Q1 · Migration motives")
    st.caption("Why do people migrate to Mexico?")

    df = views["motives"].copy()
    if df.empty:
        st.warning("View vw_top_motives is empty.")
        st.stop()
    df = df.sort_values("total_migrations", ascending=False).reset_index(drop=True)

    # ── Filters (plain columns, no HTML wrapper) ─────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        cats_avail = sorted(df["category"].dropna().unique().tolist())
        sel_cat_idx = st.selectbox(
            "Category",
            options=list(range(len(cats_avail) + 1)),
            format_func=lambda i: "All" if i == 0 else cats_avail[i - 1],
            key="q1_cat",
        )
        sel_cat = "All" if sel_cat_idx == 0 else cats_avail[sel_cat_idx - 1]
    with fc2:
        max_motives = max(4, len(df) + 1) if len(df) <= 3 else max(3, len(df))
        top_n = st.slider("Top N motives", 3, max_motives,
                            min(10, max_motives), key="q1_topn")
    with fc3:
        sort_idx = st.radio("Sort", options=[0, 1],
                            format_func=lambda i: "Most frequent" if i == 0 else "Less frequent",
                            horizontal=True, key="q1_sort")
        sort_order = "Most frequent" if sort_idx == 0 else "Less frequent"

    df_filtered = df if sel_cat == "All" else df[df["category"] == sel_cat]
    df_f = df_filtered.sort_values(
        "total_migrations", ascending=(sort_order == "Less frequent")
    ).head(top_n)

    if df_f.empty:
        st.warning(f"No motives match the category '{sel_cat}'.")
        st.stop()

    total      = int(df_f["total_migrations"].sum())
    top_motive = df_f.iloc[0]["motive"]
    top_count  = int(df_f.iloc[0]["total_migrations"])
    top_pct    = (top_count / total * 100) if total else 0
    cat_totals = df.groupby("category")["total_migrations"].sum().sort_values(ascending=False)
    lead_cat   = cat_totals.index[0]
    lead_pct   = (cat_totals.iloc[0] / cat_totals.sum() * 100) if cat_totals.sum() else 0

    hero_answer(
        "Answer",
        f'"{top_motive}" is the #1 motive ({top_pct:.1f}% of filtered set).',
        f'Leading category overall: <b>{lead_cat}</b> ({lead_pct:.1f}%). '
        f'{df["motive"].nunique()} distinct motives across {df["category"].nunique()} categories.',
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Top motive", top_motive[:20], delta=f"{top_pct:.1f}%")
        st.metric("Top category", lead_cat, delta=f"{lead_pct:.1f}%")
        st.metric("Total migrations", f"{total:,}")
        st.plotly_chart(make_donut(lead_pct, f"From {lead_cat}",
                                     color=PALETTE_CAT.get(lead_cat, PRIMARY)),
                         use_container_width=True)

    with col_c:
        st.markdown("#### Sunburst — Category → Motive")
        fig_sun = px.sunburst(
            df, path=["category", "motive"], values="total_migrations",
            color="category", color_discrete_map=PALETTE_CAT,
        )
        fig_sun.update_layout(
            height=380, paper_bgcolor="#0a0f1e", font_color="#e2e8f0",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_sun, use_container_width=True)

        st.markdown(f"#### Motives ranked  ·  category: {sel_cat}")
        df_chart = df_f.copy()
        df_chart["pct"] = (df_chart["total_migrations"] / total * 100).round(1)
        df_chart["label"] = df_chart.apply(
            lambda r: f"{int(r['total_migrations']):,} ({r['pct']}%)", axis=1)
        fig_bar = styled_bar(
            df_chart.sort_values("total_migrations"),
            x="total_migrations", y="motive",
            color_col="category", color_map=PALETTE_CAT,
            text_col="label", height=max(300, 50 + 55 * len(df_f)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_r:
        st.markdown("#### Filtered motives")
        ranked_table(df_f, "motive", "total_migrations",
                     "Motive", "Migrations", key="q1_rank")
        st.markdown("#### Category totals")
        ranked_table(cat_totals.reset_index(), "category", "total_migrations",
                     "Category", "Migrations", key="q1_cat_table")


# =============================================================================
# Q2 - Mexico vs World
# =============================================================================
elif st.session_state.page == "Q2":
    st.markdown("# Q2 · Mexico vs world")
    st.caption("What share of global migration does Mexico receive?")

    df = views["comparison"].copy()
    if df.empty:
        st.warning("View vw_international_comparison is empty.")
        st.stop()

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["total_migrants"] = pd.to_numeric(df["total_migrants"], errors="coerce")
    df = df.dropna(subset=["year", "total_migrants"])
    df["year"] = df["year"].astype(int)

    years_avail = sorted(df["year"].unique())
    mx_data = df[df["destination_country"].str.lower().str.contains("mex", na=False) &
                  (df["total_migrants"] > 0)]
    default_year = int(mx_data["year"].max()) if not mx_data.empty else int(df["year"].max())

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        ymin, ymax = int(df["year"].min()), int(df["year"].max())
        year_range = st.slider("Year range", ymin, ymax, (ymin, ymax), key="q2_year")
    with fc2:
        display_year = st.selectbox(
            "Snapshot year",
            options=years_avail[::-1],
            index=years_avail[::-1].index(default_year)
                   if default_year in years_avail else 0,
            key="q2_snap_year",
        )
    with fc3:
        top_n = st.slider("Top N countries", 5, 25, 10, key="q2_topn")

    df_f = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].copy()
    df_year = df_f[df_f["year"] == display_year].sort_values("total_migrants",
                                                                ascending=False).reset_index(drop=True)
    mx_row = df_year[df_year["destination_country"].str.lower().str.contains("mex", na=False)]

    if not mx_row.empty and float(mx_row["total_migrants"].iloc[0]) > 0:
        mx_rank = int(mx_row.index[0]) + 1
        mx_count = int(mx_row["total_migrants"].iloc[0])
        mx_share = (mx_count / df_year["total_migrants"].sum() * 100) if df_year["total_migrants"].sum() else 0
        rank_text = f"#{mx_rank} of {len(df_year)}"
    else:
        mx_rank, mx_count, mx_share = None, 0, 0
        rank_text = "Mexico not in this year"

    mx_evol = (df[df["destination_country"].str.lower().str.contains("mex", na=False)]
                  .groupby("year")["total_migrants"].sum().sort_index())
    mx_evol = mx_evol[mx_evol > 0]
    mx_total_cum = int(mx_evol.sum())

    hero_answer(
        "Answer",
        f"In {display_year}, Mexico ranks {rank_text}" +
        (f" with {mx_share:.2f}% of the migrant share." if mx_share > 0 else "."),
        f"Mexico's cumulative recorded migrants (years with data): <b>{mx_total_cum:,}</b>. "
        f"The dataset spans {ymin}–{ymax} across {df['destination_country'].nunique()} countries.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Mexico stats")
        if mx_rank:
            st.metric(f"Rank ({display_year})", f"#{mx_rank}",
                      delta=f"of {len(df_year)}")
            st.metric(f"Migrants ({display_year})", f"{mx_count:,}")
            st.metric("Cumulative", f"{mx_total_cum:,}")
            st.plotly_chart(make_donut(mx_share, f"Share {display_year}"),
                             use_container_width=True)
        else:
            st.warning(f"No Mexico data registered for {display_year}.")
            st.metric("Cumulative migrants (all years)", f"{mx_total_cum:,}")
            if not mx_evol.empty:
                latest_with_data = int(mx_evol.index.max())
                st.metric("Latest year with data", latest_with_data,
                          delta=f"{int(mx_evol.iloc[-1]):,} migrants")

    with col_c:
        st.markdown(f"#### World migration map · {display_year}")
        st.plotly_chart(make_choropleth(df_year, "destination_country",
                                          "total_migrants", height=380),
                         use_container_width=True)

        st.markdown(f"#### Top {top_n} countries · evolution over time")
        top_countries = (df_f.groupby("destination_country")["total_migrants"].sum()
                              .sort_values(ascending=False).head(top_n).index.tolist())
        if "Mexico" not in top_countries:
            top_countries.append("Mexico")
        df_top = df_f[df_f["destination_country"].isin(top_countries)]

        fig_line = px.line(
            df_top, x="year", y="total_migrants",
            color="destination_country", markers=True,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        for tr in fig_line.data:
            if tr.name and "mex" in tr.name.lower():
                tr.line.width = 5
                tr.line.color = "#3b82f6"
                tr.marker.size = 10
        fig_line.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=380,
            xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
            yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(font=dict(color="#e2e8f0", size=10)),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_r:
        st.markdown(f"#### Top destinations · {display_year}")
        ranked_table(df_year.head(top_n), "destination_country", "total_migrants",
                     "Country", "Migrants", key="q2_rank")

        if not mx_evol.empty:
            st.markdown("#### Mexico — historical trend")
            fig_mx = go.Figure()
            fig_mx.add_trace(go.Scatter(
                x=mx_evol.index, y=mx_evol.values,
                mode="lines+markers",
                line=dict(color="#3b82f6", width=3),
                marker=dict(size=8, color="#93c5fd"),
                fill="tozeroy", fillcolor="rgba(59, 130, 246, 0.2)",
            ))
            fig_mx.update_layout(
                paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                font_color="#e2e8f0", height=240,
                xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
                yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
                margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
            )
            st.plotly_chart(fig_mx, use_container_width=True)


# =============================================================================
# Q3 - Countries of origin (NEW scatter, blue progress, more filters)
# =============================================================================
elif st.session_state.page == "Q3":
    st.markdown("# Q3 · Countries of origin")
    st.caption("Where do migrants come from?")

    df = views["origin"].copy()
    if df.empty:
        st.warning("View vw_origin_countries is empty.")
        st.stop()
    df = df.sort_values("total_migrants", ascending=False).reset_index(drop=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        regions = sorted(df["region"].dropna().unique().tolist()) if "region" in df.columns else []
        sel_regs = st.multiselect("Regions", regions, default=regions, key="q3_reg")
    with fc2:
        max_countries = max(4, len(df) + 1) if len(df) <= 3 else max(3, len(df))
        top_n = st.slider("Top N countries", 3, max_countries,
                            min(10, max_countries), key="q3_topn")
    with fc3:
        min_migr = int(df["total_migrants"].min())
        max_migr = int(df["total_migrants"].max())
        if max_migr == min_migr:
            max_migr = min_migr + 1
        thresh = st.slider("Minimum migrants", min_migr, max_migr, min_migr, key="q3_thresh")

    df_f = df[df["region"].isin(sel_regs)] if sel_regs else df.copy()
    df_f = df_f[df_f["total_migrants"] >= thresh]
    if df_f.empty:
        st.warning("No countries match these filters.")
        st.stop()

    total = int(df_f["total_migrants"].sum())
    top_country = df_f.iloc[0]["origin_country"]
    top_pct = (df_f.iloc[0]["total_migrants"] / total * 100) if total else 0
    region_totals = (df_f.groupby("region")["total_migrants"].sum()
                          .sort_values(ascending=False)) if "region" in df_f.columns else pd.Series()
    top_region = region_totals.index[0] if not region_totals.empty else "—"
    top_region_pct = (region_totals.iloc[0] / total * 100) if not region_totals.empty and total else 0

    hero_answer(
        "Answer",
        f"Most migrants come from {top_country} ({top_pct:.1f}% of filtered set).",
        f"Leading region: <b>{top_region}</b> ({top_region_pct:.1f}%). "
        f"{df_f['origin_country'].nunique()} origin countries shown.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Top origin", top_country, delta=f"{top_pct:.1f}%")
        st.metric("Top region", top_region, delta=f"{top_region_pct:.1f}%")
        st.metric("Total migrants", f"{total:,}")
        st.plotly_chart(make_donut(top_region_pct, f"From {top_region}"),
                         use_container_width=True)

    with col_c:
        st.markdown("#### World map of origins")
        st.plotly_chart(make_choropleth(df_f, "origin_country",
                                          "total_migrants", height=380),
                         use_container_width=True)

        # NEW: scatter chart (size by migrants, color by region)
        st.markdown("#### Scatter — Migrants by country, sized & colored")
        df_scatter = df_f.copy().reset_index(drop=True)
        df_scatter["rank"] = df_scatter["total_migrants"].rank(ascending=False).astype(int)
        fig_scatter = px.scatter(
            df_scatter, x="rank", y="total_migrants",
            size="total_migrants", color="region",
            hover_name="origin_country",
            color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT, DARK, "#cbd5e1"],
            size_max=60,
        )
        fig_scatter.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0", height=320,
            xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "Rank position"},
            yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": "Migrants"},
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_r:
        st.markdown(f"#### Top {top_n} countries")
        ranked_table(df_f.head(top_n), "origin_country", "total_migrants",
                     "Country", "Migrants", key="q3_rank")
        if not region_totals.empty:
            st.markdown("#### By region")
            ranked_table(region_totals.reset_index(), "region", "total_migrants",
                         "Region", "Migrants", key="q3_reg_t")


# =============================================================================
# Q4 - Risks (varied charts: bar + pie + radar)
# =============================================================================
elif st.session_state.page == "Q4":
    st.markdown("# Q4 · Risks and threats")
    st.caption("What risks do migrants face in Mexico?")

    df = views["risks"].copy()
    if df.empty:
        st.warning("View vw_migrant_risks is empty.")
        st.stop()
    df = df.sort_values("cases", ascending=False).reset_index(drop=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        types = sorted(df["risk_type"].dropna().unique().tolist())
        sel_t_idx = st.multiselect(
            "Risk types",
            options=list(range(len(types))),
            default=list(range(len(types))),
            format_func=lambda i: types[i],
            key="q4_type",
        )
        sel_t = [types[i] for i in sel_t_idx]
    with fc2:
        max_risks = max(4, len(df) + 1) if len(df) <= 3 else max(3, len(df))
        top_n = st.slider("Top N risks", 3, max_risks,
                            min(10, max_risks), key="q4_topn")
    with fc3:
        min_cases = int(df["cases"].min())
        max_cases = int(df["cases"].max())
        if max_cases == min_cases:
            max_cases = min_cases + 1
        case_thresh = st.slider("Minimum cases", min_cases, max_cases,
                                  min_cases, key="q4_thresh")

    df_f = df[df["risk_type"].isin(sel_t)] if sel_t else df.copy()
    df_f = df_f[df_f["cases"] >= case_thresh]
    if df_f.empty:
        st.warning("No risks match these filters.")
        st.stop()

    total = int(df_f["cases"].sum())
    type_totals = df_f.groupby("risk_type")["cases"].sum().sort_values(ascending=False)
    lead_type = type_totals.index[0]
    lead_pct = (type_totals.iloc[0] / total * 100) if total else 0
    top_risk = df_f.iloc[0]["risk"]
    top_pct = (df_f.iloc[0]["cases"] / total * 100) if total else 0

    hero_answer(
        "Answer",
        f"<b>{lead_type}</b> risks dominate ({lead_pct:.1f}% of all cases).",
        f'Most frequent specific risk: "{top_risk[:60]}" ({top_pct:.1f}%). '
        f"{df_f['risk'].nunique()} distinct risks documented.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Total cases", f"{total:,}")
        st.metric("Top risk type", lead_type, delta=f"{lead_pct:.1f}%")
        st.metric("Risk types", f"{df_f['risk_type'].nunique()}")
        # NEW: pie chart (not donut) for type breakdown
        st.markdown("#### By type (pie)")
        fig_pie = px.pie(
            type_totals.reset_index(), names="risk_type", values="cases",
            color="risk_type", color_discrete_map=PALETTE_RISK,
        )
        fig_pie.update_traces(textfont=dict(color="#dbeafe", size=12),
                                textinfo="label+percent")
        fig_pie.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=240,
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_c:
        st.markdown(f"#### Top {top_n} risks")
        df_chart = df_f.head(top_n).copy()
        df_chart["pct"] = (df_chart["cases"] / total * 100).round(1)
        df_chart["label"] = df_chart.apply(lambda r: f"{int(r['cases'])} ({r['pct']}%)", axis=1)
        fig = styled_bar(
            df_chart.sort_values("cases"),
            x="cases", y="risk",
            color_col="risk_type", color_map=PALETTE_RISK,
            text_col="label", height=max(320, 50 + 35 * len(df_chart)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # NEW: radar chart for risk-type profile
        st.markdown("#### Radar — Risk type profile")
        all_types = list(PALETTE_RISK.keys())
        type_vals = [int(df_f[df_f["risk_type"] == t]["cases"].sum()) for t in all_types]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=type_vals + [type_vals[0]],
            theta=all_types + [all_types[0]],
            fill="toself",
            line=dict(color="#3b82f6", width=3),
            fillcolor="rgba(59, 130, 246, 0.3)",
            name="Risk profile",
        ))
        fig_radar.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=340,
            polar=dict(
                bgcolor="#0f1a35",
                radialaxis=dict(visible=True, gridcolor="#1e3a8a",
                                  color="#94a3b8"),
                angularaxis=dict(gridcolor="#1e3a8a", color="#dbeafe"),
            ),
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_r:
        st.markdown("#### All risks ranked")
        ranked_table(df_f, "risk", "cases", "Risk", "Cases", key="q4_rank")
        st.markdown("#### By type")
        ranked_table(type_totals.reset_index(), "risk_type", "cases",
                     "Type", "Cases", key="q4_type_t")


# =============================================================================
# Q5 - Impact analysis (more filters)
# =============================================================================
elif st.session_state.page == "Q5":
    st.markdown("# Q5 · Impact analysis")
    st.caption("Social and economic impact on Mexico")

    df = views["impacts"].copy()
    df_d = views["demographic"].copy()
    if df.empty:
        st.warning("View vw_impacts_on_mexico is empty.")
        st.stop()
    df = df.sort_values("frequency", ascending=False).reset_index(drop=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        types = sorted(df["impact_type"].dropna().unique().tolist())
        sel_t = st.multiselect("Impact types", types, default=types, key="q5_type")
    with fc2:
        if not df_d.empty:
            sexes = sorted(df_d["sex"].dropna().unique().tolist())
            sel_sex = st.multiselect("Sex (demographics)", sexes, default=sexes,
                                       key="q5_sex")
        else:
            sel_sex = []
    with fc3:
        if not df_d.empty:
            levels = sorted(df_d["socioeconomic_level"].dropna().unique().tolist())
            sel_levels = st.multiselect("Socioeconomic levels", levels, default=levels,
                                          key="q5_lvl")
        else:
            sel_levels = []

    df_f = df[df["impact_type"].isin(sel_t)] if sel_t else df.copy()
    df_df = df_d.copy() if not df_d.empty else df_d
    if not df_df.empty and sel_sex:
        df_df = df_df[df_df["sex"].isin(sel_sex)]
    if not df_df.empty and sel_levels:
        df_df = df_df[df_df["socioeconomic_level"].isin(sel_levels)]

    if df_f.empty:
        st.warning("No impacts match these filters.")
        st.stop()

    total = int(df_f["frequency"].sum())
    type_totals = df_f.groupby("impact_type")["frequency"].sum().sort_values(ascending=False)
    lead_type = type_totals.index[0]
    lead_pct = (type_totals.iloc[0] / total * 100) if total else 0
    social_total = int(type_totals.get("Social", 0))
    econ_total = int(type_totals.get("Economic", 0))

    hero_answer(
        "Answer",
        f"Mexico shows {social_total:,} social and {econ_total:,} economic impact records.",
        f"<b>{lead_type}</b> impacts represent {lead_pct:.1f}% of the total. "
        f"{df_f['impact'].nunique()} distinct categories tracked.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Social impacts", f"{social_total:,}")
        st.metric("Economic impacts", f"{econ_total:,}")
        st.metric("Total records", f"{total:,}")
        st.plotly_chart(make_donut(lead_pct, f"{lead_type} share",
                                     color=PALETTE_IMPACT.get(lead_type, PRIMARY)),
                         use_container_width=True)

    with col_c:
        st.markdown("#### Impact catalog · ranked")
        df_chart = df_f.copy()
        df_chart["pct"] = (df_chart["frequency"] / total * 100).round(1)
        df_chart["label"] = df_chart.apply(lambda r: f"{int(r['frequency'])} ({r['pct']}%)", axis=1)
        fig = styled_bar(
            df_chart.sort_values("frequency"),
            x="frequency", y="impact",
            color_col="impact_type", color_map=PALETTE_IMPACT,
            text_col="label", height=max(280, 50 + 55 * len(df_chart)),
        )
        st.plotly_chart(fig, use_container_width=True)

        if not df_df.empty:
            st.markdown("#### Demographic heatmap · Sex × Level")
            pivot = df_df.pivot_table(index="sex", columns="socioeconomic_level",
                                        values="total", aggfunc="sum", fill_value=0)
            fig_heat = go.Figure(data=go.Heatmap(
                z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                colorscale=BLUE_SCALE, text=pivot.values, texttemplate="%{text}",
                textfont={"color": "#dbeafe", "size": 16},
                showscale=False,
            ))
            fig_heat.update_layout(
                paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                font_color="#e2e8f0", height=300,
                xaxis_title="Socioeconomic level", yaxis_title="Sex",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    with col_r:
        st.markdown("#### Impacts ranked")
        ranked_table(df_f, "impact", "frequency",
                     "Impact", "Frequency", key="q5_rank")
        if not df_df.empty:
            st.markdown("#### Demographics filtered")
            df_demo_show = df_df.copy()
            df_demo_show["group"] = df_demo_show["sex"] + " · " + df_demo_show["socioeconomic_level"]
            df_demo_show = df_demo_show.sort_values("total", ascending=False)
            ranked_table(df_demo_show, "group", "total",
                         "Sex · Level", "Migrants", key="q5_demo")


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption(
    "Migration Intelligence Dashboard v7.0  ·  UABC  ·  "
    "Sources: INEGI ENADID 2023 · UN DESA 2024 · World Bank · UNHCR · IOM"
)
