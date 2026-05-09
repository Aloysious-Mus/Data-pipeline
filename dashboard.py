"""
Patent Analysis Dashboard - Streamlit App
Run with: python -m streamlit run dashboard.py
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Patent Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

DB_PATH = os.path.join("data", "patents.db")

# ── DB helper ──────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Running query...")
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

# ── Get year range ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_year_range():
    df = run_query("SELECT MIN(filing_year) as mn, MAX(filing_year) as mx FROM patents WHERE filing_year > 1900")
    return int(df.iloc[0, 0]), int(df.iloc[0, 1])

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("📊 Patent Analytics")
st.sidebar.markdown("---")

min_year, max_year = get_year_range()
year_range = st.sidebar.slider(
    "📅 Year Range",
    min_value=min_year, max_value=max_year,
    value=(2010, max_year), step=1
)
y1, y2 = year_range

top_n = st.sidebar.slider("🔢 Top N Results", min_value=5, max_value=25, value=10)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Showing:** {y1} – {y2}")
st.sidebar.markdown("**Source:** USPTO Patent Database")

# ── Title ──────────────────────────────────────────────────────────────────────
st.title("📊 Patent Analysis Dashboard")
st.markdown(f"Exploring USPTO patent data from **{y1}** to **{y2}**.")
st.markdown("---")

# ── KPI Cards — fast queries, no JOINs ────────────────────────────────────────
st.subheader("📌 Summary Statistics")
with st.spinner("Loading summary stats..."):
    total_patents = run_query(
        "SELECT COUNT(*) AS n FROM patents WHERE filing_year BETWEEN ? AND ?",
        (y1, y2)
    ).iloc[0, 0]

    total_inventors = run_query(
        "SELECT COUNT(DISTINCT inventor_id) AS n FROM inventors WHERE patent_id IN (SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?)",
        (y1, y2)
    ).iloc[0, 0]

    total_companies = run_query(
        "SELECT COUNT(DISTINCT company_id) AS n FROM assignees WHERE patent_id IN (SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?)",
        (y1, y2)
    ).iloc[0, 0]

    total_countries = run_query(
        "SELECT COUNT(DISTINCT country) AS n FROM inventors WHERE country IS NOT NULL AND country != '' AND patent_id IN (SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?)",
        (y1, y2)
    ).iloc[0, 0]

    avg_per_year = round(total_patents / max(1, y2 - y1 + 1), 0)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📄 Patents",           f"{total_patents:,}")
k2.metric("👤 Inventors",         f"{total_inventors:,}")
k3.metric("🏢 Companies",         f"{total_companies:,}")
k4.metric("🌍 Countries",         f"{total_countries:,}")
k5.metric("📅 Avg Patents/Year",  f"{avg_per_year:,.0f}")
st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Trend",
    "👤 Inventors",
    "🏢 Companies",
    "🌍 Countries",
    "🔍 Explorer",
    "🔗 Multi-Company",
    "🏆 Rankings"
])

# ── Tab 1: Yearly Trend ────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Patent Filing Trend ({y1}–{y2})")
    with st.spinner("Loading trend data..."):
        df_trend = run_query(
            "SELECT filing_year, COUNT(*) AS patent_count FROM patents WHERE filing_year BETWEEN ? AND ? GROUP BY filing_year ORDER BY filing_year",
            (y1, y2)
        )
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.area(
            df_trend, x="filing_year", y="patent_count",
            labels={"filing_year": "Year", "patent_count": "Patents Filed"},
            title="Patents Filed Per Year"
        )
        fig.update_traces(line_color="#6366F1", fillcolor="rgba(99,102,241,0.15)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 📊 Insights")
        peak = df_trend.loc[df_trend["patent_count"].idxmax()]
        low  = df_trend.loc[df_trend["patent_count"].idxmin()]
        growth = ((df_trend.iloc[-1]["patent_count"] / max(1, df_trend.iloc[0]["patent_count"])) - 1) * 100
        st.metric("Peak Year",   f"{int(peak['filing_year'])}", f"{int(peak['patent_count']):,} patents")
        st.metric("Lowest Year", f"{int(low['filing_year'])}",  f"{int(low['patent_count']):,} patents")
        st.metric("Growth",      f"{growth:+.1f}%")
    st.dataframe(df_trend, use_container_width=True, hide_index=True)

# ── Tab 2: Top Inventors ───────────────────────────────────────────────────────
with tab2:
    st.subheader(f"Top {top_n} Inventors ({y1}–{y2})")
    with st.spinner("Loading inventors..."):
        df_inv = run_query(f"""
            SELECT i.inventor_name, i.country,
                   COUNT(DISTINCT i.patent_id) AS patent_count
            FROM inventors i
            WHERE i.inventor_name IS NOT NULL AND i.inventor_name != ''
              AND i.patent_id IN (
                  SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?
              )
            GROUP BY i.inventor_id, i.inventor_name, i.country
            ORDER BY patent_count DESC
            LIMIT {top_n}
        """, (y1, y2))
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.bar(
            df_inv, x="patent_count", y="inventor_name",
            orientation="h", color="country",
            labels={"patent_count": "Patents", "inventor_name": "Inventor"},
            title=f"Top {top_n} Inventors"
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 🥇 Top 5")
        for i, row in df_inv.head(5).iterrows():
            st.markdown(f"**#{i+1}** {row['inventor_name']}  \n`{row['patent_count']:,}` · {row['country'] or 'N/A'}")
            st.markdown("---")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

# ── Tab 3: Top Companies ───────────────────────────────────────────────────────
with tab3:
    st.subheader(f"Top {top_n} Companies ({y1}–{y2})")
    with st.spinner("Loading companies..."):
        df_comp = run_query(f"""
            SELECT a.company_name, COUNT(DISTINCT a.patent_id) AS patent_count
            FROM assignees a
            WHERE a.company_name IS NOT NULL AND a.company_name != ''
              AND a.patent_id IN (
                  SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?
              )
            GROUP BY a.company_id, a.company_name
            ORDER BY patent_count DESC
            LIMIT {top_n}
        """, (y1, y2))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            df_comp, x="patent_count", y="company_name", orientation="h",
            labels={"patent_count": "Patents", "company_name": "Company"},
            title=f"Top {top_n} Companies"
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        fig.update_traces(marker_color="#10B981")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.pie(df_comp, names="company_name", values="patent_count", title="Market Share")
        st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

# ── Tab 4: Top Countries ───────────────────────────────────────────────────────
with tab4:
    st.subheader(f"Top {top_n} Countries ({y1}–{y2})")
    with st.spinner("Loading countries..."):
        df_ctry = run_query(f"""
            SELECT i.country, COUNT(DISTINCT i.patent_id) AS patent_count
            FROM inventors i
            WHERE i.country IS NOT NULL AND i.country != ''
              AND i.patent_id IN (
                  SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?
              )
            GROUP BY i.country
            ORDER BY patent_count DESC
            LIMIT {top_n}
        """, (y1, y2))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_ctry, x="country", y="patent_count",
                     labels={"patent_count": "Patents", "country": "Country"},
                     title=f"Top {top_n} Countries")
        fig.update_traces(marker_color="#F59E0B")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.pie(df_ctry, names="country", values="patent_count", title="Share by Country")
        st.plotly_chart(fig2, use_container_width=True)

    # Top 5 country trend
    with st.spinner("Loading country trends..."):
        top5 = df_ctry["country"].head(5).tolist()
        placeholders = ",".join(["?" for _ in top5])
        df_ctry_trend = run_query(f"""
            SELECT p.filing_year, i.country, COUNT(DISTINCT i.patent_id) AS patent_count
            FROM inventors i
            JOIN patents p ON i.patent_id = p.patent_id
            WHERE p.filing_year BETWEEN ? AND ? AND i.country IN ({placeholders})
            GROUP BY p.filing_year, i.country ORDER BY p.filing_year
        """, (y1, y2, *top5))
    fig3 = px.line(df_ctry_trend, x="filing_year", y="patent_count", color="country",
                   title="Top 5 Countries — Trend Over Time")
    st.plotly_chart(fig3, use_container_width=True)
    st.dataframe(df_ctry, use_container_width=True, hide_index=True)

# ── Tab 5: Patent Explorer ─────────────────────────────────────────────────────
with tab5:
    st.subheader("🔍 Patent Explorer")
    search = st.text_input("Search patent titles", placeholder="e.g. semiconductor, battery, AI...")
    with st.spinner("Loading patents..."):
        base_sql = """
            SELECT p.patent_id, p.title, p.filing_year,
                   i.inventor_name, i.country AS inventor_country, a.company_name
            FROM patents p
            LEFT JOIN inventors i ON p.patent_id = i.patent_id
            LEFT JOIN assignees a ON p.patent_id = a.patent_id
            WHERE p.filing_year BETWEEN ? AND ?
        """
        params = [y1, y2]
        if search:
            base_sql += " AND p.title LIKE ?"
            params.append(f"%{search}%")
        base_sql += " LIMIT 200"
        df_exp = run_query(base_sql, tuple(params))
    st.markdown(f"Showing **{len(df_exp):,}** results")
    st.dataframe(df_exp, use_container_width=True, hide_index=True)

# ── Tab 6: Multi-Company Inventors ─────────────────────────────────────────────
with tab6:
    st.subheader(f"Inventors Across Multiple Companies ({y1}–{y2})")
    st.caption("Inventors with patents assigned to more than one company.")
    with st.spinner("Running CTE query..."):
        df_multi = run_query(f"""
            WITH icc AS (
                SELECT i.inventor_id,
                       COUNT(DISTINCT a.company_id) AS company_count,
                       COUNT(DISTINCT i.patent_id)  AS patent_count
                FROM inventors i
                JOIN assignees a ON i.patent_id = a.patent_id
                WHERE i.patent_id IN (
                    SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?
                )
                GROUP BY i.inventor_id
                HAVING COUNT(DISTINCT a.company_id) > 1
            )
            SELECT i.inventor_name, i.country, icc.patent_count, icc.company_count
            FROM icc JOIN inventors i ON icc.inventor_id = i.inventor_id
            ORDER BY icc.patent_count DESC
            LIMIT {top_n}
        """, (y1, y2))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(df_multi, x="company_count", y="patent_count",
                         hover_name="inventor_name", color="country", size="patent_count",
                         title="Patents vs Companies per Inventor")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(df_multi, x="inventor_name", y="company_count", color="country",
                      title="Companies per Inventor")
        fig2.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df_multi, use_container_width=True, hide_index=True)

# ── Tab 7: Rankings ────────────────────────────────────────────────────────────
with tab7:
    st.subheader(f"Inventor Rankings ({y1}–{y2})")
    with st.spinner("Running ranking query..."):
        df_rank = run_query(f"""
            WITH ip AS (
                SELECT i.inventor_id, i.inventor_name, i.country,
                       COUNT(DISTINCT i.patent_id) AS patent_count
                FROM inventors i
                WHERE i.patent_id IN (
                    SELECT patent_id FROM patents WHERE filing_year BETWEEN ? AND ?
                )
                GROUP BY i.inventor_id, i.inventor_name, i.country
            )
            SELECT inventor_name, country, patent_count,
                   RANK() OVER (ORDER BY patent_count DESC) AS world_rank,
                   RANK() OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank
            FROM ip ORDER BY patent_count DESC
            LIMIT {top_n}
        """, (y1, y2))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🌐 World Rankings")
        st.dataframe(df_rank[["world_rank","inventor_name","country","patent_count"]],
                     use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### 🏅 Country Rankings")
        st.dataframe(df_rank[["country_rank","inventor_name","country","patent_count"]],
                     use_container_width=True, hide_index=True)
    fig = px.bar(df_rank, x="inventor_name", y="patent_count", color="country",
                 text="world_rank", title=f"Top {top_n} Ranked Inventors")
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Patent Analysis Dashboard · {y1}–{y2} · Streamlit & Plotly · USPTO Data")