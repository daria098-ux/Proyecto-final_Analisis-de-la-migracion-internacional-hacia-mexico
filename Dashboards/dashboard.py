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

    # Filters - only category + sort (Top N removed: too few motives)
    fc1, fc2 = st.columns(2)
    with fc1:
        cats_avail = ["All"] + sorted(df["category"].dropna().unique().tolist())
        sel_cat = st.selectbox("Category", cats_avail, key="q1_cat")
    with fc2:
        sort_order = st.radio("Sort", ["Most frequent", "Less frequent"],
                                horizontal=True, key="q1_sort")

    df_filtered = df if sel_cat == "All" else df[df["category"] == sel_cat]
    df_f = df_filtered.sort_values(
        "total_migrations", ascending=(sort_order == "Less frequent")
    )

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

    # New layout:
    # Left column: highlights + circular chart (replaces sunburst).
    # Right column: motives ranked bar chart on top, tables below.
    col_l, col_r = st.columns([1.4, 2.6])

    with col_l:
        st.markdown("#### Highlights")
        m1, m2 = st.columns(2)
        m1.metric("Top motive", top_motive[:18], delta=f"{top_pct:.1f}%")
        m2.metric("Top category", lead_cat, delta=f"{lead_pct:.1f}%")
        st.metric("Total migrations", f"{total:,}")

        # Circular chart that replaces the sunburst - clearer view of
        # category share. Pull-out the leading slice for emphasis.
        st.markdown("#### Category share")
        cat_df = cat_totals.reset_index()
        cat_df.columns = ["category", "total"]
        pulls = [0.08 if c == lead_cat else 0 for c in cat_df["category"]]
        colors = [PALETTE_CAT.get(c, PRIMARY) for c in cat_df["category"]]
        fig_pie = go.Figure(go.Pie(
            labels=cat_df["category"], values=cat_df["total"],
            hole=0.45, pull=pulls,
            marker=dict(colors=colors, line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#dbeafe", size=13),
            sort=False,
        ))
        fig_pie.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=340,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(font=dict(color="#e2e8f0", size=11),
                        orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_r:
        # Motives ranked chart - moved to the top-right for visibility.
        st.markdown(f"#### Motives ranked  ·  category: {sel_cat}")
        df_chart = df_f.copy()
        df_chart["pct"] = (df_chart["total_migrations"] / total * 100).round(1)
        df_chart["label"] = df_chart.apply(
            lambda r: f"{int(r['total_migrations']):,} ({r['pct']}%)", axis=1)
        fig_bar = styled_bar(
            df_chart.sort_values("total_migrations"),
            x="total_migrations", y="motive",
            color_col="category", color_map=PALETTE_CAT,
            text_col="label", height=max(280, 50 + 70 * len(df_f)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Tables - pushed below the ranked chart.
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### Filtered motives")
            ranked_table(df_f, "motive", "total_migrations",
                         "Motive", "Migrations", key="q1_rank")
        with t2:
            st.markdown("#### Category totals")
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

    years_avail = sorted(df["year"].unique())
    mx_data = df[df["destination_country"].str.lower().str.contains("mex", na=False) &
                  (df["total_migrants"] > 0)]
    default_year = int(mx_data["year"].max()) if not mx_data.empty else int(df["year"].max())

    # Available countries to compare against Mexico (Mexico excluded
    # from the multiselect because it's always plotted).
    countries_all = sorted([c for c in df["destination_country"].dropna().unique()
                            if "mex" not in c.lower()])
    # Default comparison: top 3 (excl. Mexico) by total migrants.
    default_top3 = (df[~df["destination_country"].str.lower().str.contains("mex", na=False)]
                      .groupby("destination_country")["total_migrants"].sum()
                      .sort_values(ascending=False).head(3).index.tolist())

    fc1, fc2, fc3, fc4 = st.columns([1.4, 1.2, 1.2, 2.2])
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
        top_n = st.slider("Top N (snapshot)", 5, 25, 10, key="q2_topn")
    with fc4:
        compare_countries = st.multiselect(
            "Compare vs Mexico",
            countries_all,
            default=default_top3,
            help="Pick the countries to plot alongside Mexico in the evolution chart.",
            key="q2_compare",
        )

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
        f"The dataset spans {ymin}-{ymax} across {df['destination_country'].nunique()} countries.",
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

        # Evolution: Mexico vs the countries chosen in the multiselect
        # (default = top 3). Keeps the chart readable and answers the
        # "Mexico vs world" question directly.
        # Resolve Mexico's exact label (could be "Mexico" or similar).
        mex_label_series = df_f[df_f["destination_country"]
                                .str.lower().str.contains("mex", na=False)]["destination_country"]
        mex_label = mex_label_series.iloc[0] if not mex_label_series.empty else "Mexico"
        sel_set = list({*compare_countries, mex_label})

        if not compare_countries:
            st.info("Pick at least one country in the multiselect above to compare against Mexico.")
        else:
            st.markdown(
                f"#### Mexico vs {len(compare_countries)} selected "
                f"countries · evolution {year_range[0]}-{year_range[1]}"
            )
            df_top = df_f[df_f["destination_country"].isin(sel_set)]
            fig_line = px.line(
                df_top, x="year", y="total_migrants",
                color="destination_country", markers=True,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            # Highlight Mexico with a thick blue line.
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
                legend=dict(title="Country", font=dict(color="#e2e8f0", size=11)),
            )
            st.plotly_chart(fig_line, use_container_width=True,
                            config={"scrollZoom": False})

    with col_r:
        st.markdown(f"#### Top destinations · {display_year}")
        ranked_table(df_year.head(top_n), "destination_country", "total_migrants",
                     "Country", "Migrants", key="q2_rank")

        if not mx_evol.empty:
            st.markdown("#### Mexico - historical trend")
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

    fc1, fc2, fc3 = st.columns([2, 1.4, 1.4])
    with fc1:
        sel_countries = st.multiselect(
            "Origin countries",
            countries_all, default=countries_all,
            help="Pick which origin countries to include.",
            key="q3_countries",
        )
    with fc2:
        if not df_cmp_all.empty:
            ymin = int(df_cmp_all["year"].min())
            ymax = int(df_cmp_all["year"].max())
            year_range = st.slider("Year range (evolution)", ymin, ymax,
                                   (ymin, ymax), key="q3_year")
        else:
            year_range = None
    with fc3:
        min_migr = int(df["total_migrants"].min())
        max_migr = int(df["total_migrants"].max())
        thresh = st.slider("Minimum migrants", min_migr, max_migr, min_migr, key="q3_thresh")

    df_f = df[df["origin_country"].isin(sel_countries)] if sel_countries else df.copy()
    df_f = df_f[df_f["total_migrants"] >= thresh]
    if df_f.empty:
        st.warning("No countries match these filters.")
        st.stop()

    total = int(df_f["total_migrants"].sum())
    top_country = df_f.iloc[0]["origin_country"]
    top_pct = (df_f.iloc[0]["total_migrants"] / total * 100) if total else 0

    hero_answer(
        "Answer",
        f"Most migrants come from {top_country} ({top_pct:.1f}% of selection).",
        f"{df_f['origin_country'].nunique()} origin countries shown. "
        f"Total recorded migrants in selection: <b>{total:,}</b>.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Top origin", top_country, delta=f"{top_pct:.1f}%")
        st.metric("Countries", f"{df_f['origin_country'].nunique()}")
        st.metric("Total migrants", f"{total:,}")
        st.plotly_chart(make_donut(top_pct, f"From {top_country[:14]}"),
                         use_container_width=True)

    with col_c:
        st.markdown("#### World map of origins")
        st.plotly_chart(make_choropleth(df_f, "origin_country",
                                          "total_migrants", height=380),
                         use_container_width=True)

        # Evolution chart using the comparison view (gives us the
        # time dimension that the origin view itself lacks).
        if year_range is not None:
            st.markdown(
                f"#### Evolution of selected countries · {year_range[0]}-{year_range[1]}"
            )
        else:
            st.markdown("#### Evolution of selected countries")

        if df_cmp_all.empty or year_range is None:
            st.info("Comparison data not available - evolution chart skipped.")
        else:
            df_evol = df_cmp_all[
                df_cmp_all["destination_country"].isin(sel_countries) &
                (df_cmp_all["year"] >= year_range[0]) &
                (df_cmp_all["year"] <= year_range[1])
            ]
            if df_evol.empty:
                st.info("No comparison records for the selected countries / years.")
            else:
                fig_evol = px.line(
                    df_evol, x="year", y="total_migrants",
                    color="destination_country", markers=True,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_evol.update_layout(
                    paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                    font_color="#e2e8f0", height=320,
                    xaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
                    yaxis={"color": "#94a3b8", "gridcolor": "#1e293b", "title": None},
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(title="Country", font=dict(color="#e2e8f0", size=11)),
                )
                st.plotly_chart(fig_evol, use_container_width=True,
                                config={"scrollZoom": False})

    with col_r:
        st.markdown("#### Selected countries · ranked")
        ranked_table(df_f, "origin_country", "total_migrants",
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

    # Filters
    fc1, fc2, fc3 = st.columns([2, 1.2, 1.2])
    with fc1:
        sel_risks = st.multiselect(
            "Specific risks",
            ATOMIC_RISKS, default=ATOMIC_RISKS,
            help="Pick which physical risks to analyse.",
            key="q4_risks",
        )
    with fc2:
        view_mode = st.radio(
            "View", ["All", "Single risks", "Combined risks"],
            horizontal=False, key="q4_mode",
        )
    with fc3:
        sort_by = st.radio(
            "Sort", ["Most cases", "Fewest cases"],
            horizontal=False, key="q4_sort",
        )

    # Apply filters
    if view_mode == "Single risks":
        df_f = df[~df["is_combo"]].copy()
    elif view_mode == "Combined risks":
        df_f = df[df["is_combo"]].copy()
    else:
        df_f = df.copy()

    # Keep rows that contain at least one selected risk
    if sel_risks:
        df_f = df_f[df_f["atoms"].apply(
            lambda atoms: any(a in sel_risks for a in atoms)
        )]

    if df_f.empty:
        st.warning("No risks match these filters.")
        st.stop()

    df_f = df_f.sort_values(
        "cases", ascending=(sort_by == "Fewest cases")
    )

    # Per-atomic-risk totals (cases where each atom appears, alone or in combos)
    risk_totals = {}
    for r in ATOMIC_RISKS:
        risk_totals[r] = int(df[df["atoms"].apply(lambda atoms: r in atoms)]
                               ["cases"].sum())
    risk_totals_s = pd.Series(risk_totals).sort_values(ascending=False)

    # KPIs
    total_filtered = int(df_f["cases"].sum())
    total_all = int(df["cases"].sum())
    df_single_all = df[~df["is_combo"]]
    df_combo_all  = df[df["is_combo"]]
    combo_share = (df_combo_all["cases"].sum() / total_all * 100) if total_all else 0
    top_atom = risk_totals_s.index[0]
    top_atom_val = int(risk_totals_s.iloc[0])

    hero_answer(
        "Answer",
        f'"{top_atom}" is the most documented risk '
        f"({top_atom_val} cases counting solo + combined records).",
        f"{len(ATOMIC_RISKS)} distinct physical risks. "
        f"<b>{combo_share:.1f}%</b> of all cases involve multiple risks "
        f"co-occurring on the same migrant.",
    )

    col_l, col_c, col_r = st.columns([1.2, 2.6, 1.6])

    with col_l:
        st.markdown("#### Highlights")
        st.metric("Total cases (filtered)", f"{total_filtered:,}")
        st.metric("Most documented", top_atom[:22], delta=f"{top_atom_val} cases")
        st.metric("Distinct risks", f"{len(ATOMIC_RISKS)}")
        st.metric("Combined cases share", f"{combo_share:.1f}%")

        st.markdown("#### Single vs combined")
        sc_df = pd.DataFrame({
            "kind": ["Single risk", "Multiple risks"],
            "cases": [int(df_single_all["cases"].sum()),
                      int(df_combo_all["cases"].sum())],
        })
        fig_sc = go.Figure(go.Pie(
            labels=sc_df["kind"], values=sc_df["cases"],
            hole=0.55,
            marker=dict(colors=["#3b82f6", "#93c5fd"],
                        line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#dbeafe", size=12),
        ))
        fig_sc.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=240,
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_c:
        st.markdown("#### Radar - Physical risk profile")
        radar_risks = [r for r in ATOMIC_RISKS if r in sel_risks]
        if len(radar_risks) < 3:
            st.info("Pick at least 3 risks above to draw the radar.")
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
                name="Cases (alone + combined)",
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

        # Bar chart of filtered rows
        st.markdown(f"#### Filtered rows - view: {view_mode}")
        df_chart = df_f.copy()
        df_chart["pct"] = (df_chart["cases"] / total_filtered * 100).round(1)
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
            color_discrete_map={"Single": "#3b82f6", "Combined": "#93c5fd"},
            text="label",
        )
        fig_bar.update_traces(textposition="outside",
                              textfont=dict(color="#dbeafe", size=11))
        fig_bar.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
            font_color="#e2e8f0",
            height=max(320, 50 + 30 * len(df_chart)),
            yaxis={"categoryorder": "total ascending",
                   "title": None, "color": "#94a3b8"},
            xaxis={"title": "Cases", "color": "#94a3b8", "gridcolor": "#1e293b"},
            margin=dict(t=10, b=10, l=10, r=40),
            legend=dict(title="Type", font=dict(color="#e2e8f0", size=11)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_r:
        st.markdown("#### Atomic risks - global ranking")
        rk_df = risk_totals_s.reset_index()
        rk_df.columns = ["risk", "cases"]
        ranked_table(rk_df, "risk", "cases", "Risk", "Cases", key="q4_rank")

        # Co-occurrence count: how many combo rows include each atom?
        st.markdown("#### Combo presence per risk")
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

    COLOR_MX = "#3b82f6"   # blue
    COLOR_CU = "#f59e0b"   # amber

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

    # ── Filters ─────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2, 1.3, 1.3, 1.3])
    with fc1:
        year_range = st.slider("Year range", ymin, ymax, (ymin, ymax),
                               key="q5_year")
    with fc2:
        metric = st.selectbox(
            "Main metric",
            ["Total migrants", "World share (%)"],
            key="q5_metric",
        )
    with fc3:
        chart_kind = st.radio(
            "Evolution chart", ["Lines", "Bars", "Area"],
            horizontal=False, key="q5_kind",
        )
    with fc4:
        show_cum = st.toggle("Cumulative", value=False, key="q5_cum",
                              help="Plot cumulative totals over time.")

    df_mx_f = df_mx[(df_mx["year"] >= year_range[0]) &
                    (df_mx["year"] <= year_range[1])].copy()
    df_cu_f = df_cu[(df_cu["year"] >= year_range[0]) &
                    (df_cu["year"] <= year_range[1])].copy()

    if df_mx_f.empty or df_cu_f.empty:
        st.warning("No data for the selected year range.")
        st.stop()

    y_col = "total_migrants" if metric == "Total migrants" else "world_percentage"
    y_title = "Migrants" if y_col == "total_migrants" else "% of world"

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
        fig_share = go.Figure(go.Pie(
            labels=["Mexico", "Cuba"],
            values=[mx_total, cu_total],
            hole=0.55,
            marker=dict(colors=[COLOR_MX, COLOR_CU],
                        line=dict(color="#0a0f1e", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#dbeafe", size=14),
        ))
        fig_share.update_layout(
            paper_bgcolor="#0a0f1e", font_color="#e2e8f0", height=200,
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
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
        st.caption("IOM physical risks scaled by each country's migration "
                   "volume in the selected range.")
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
            # Mexico = baseline, Cuba = scaled by migration ratio
            scale = (cu_total / mx_total) if mx_total else 1
            r_vals_cu = [round(v * scale) for v in r_vals]
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
                fillcolor="rgba(245, 158, 11, 0.25)",
                name="Cuba (scaled)",
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
        st.markdown("#### Cuba → Mexico flow (vs other origins)")
        st.caption("Top origin countries arriving in Mexico — Cuba leads.")
        if not df_org.empty:
            df_org_show = df_org.sort_values("total_migrants",
                                              ascending=False).head(6).copy()
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


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption(
    "Migration Intelligence Dashboard v8.0  ·  UABC  ·  "
    "Sources: INEGI ENADID 2023 · UN DESA 2024 · World Bank · UNHCR · IOM"
)