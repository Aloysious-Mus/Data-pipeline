"""
Patent Analysis Dashboard - Streamlit App
Reads from CSV files in Reports/ folder (no database needed)
Run with: python -m streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Patent Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

REPORTS_DIR = "Reports"

@st.cache_data(show_spinner="Loading data...")
def load_data():
    patents   = pd.read_csv(os.path.join(REPORTS_DIR, "clean_patents.csv"),   dtype=str)
    inventors = pd.read_csv(os.path.join(REPORTS_DIR, "clean_inventors.csv"), dtype=str)
    companies = pd.read_csv(os.path.join(REPORTS_DIR, "clean_companies.csv"), dtype=str)
    trends    = pd.read_csv(os.path.join(REPORTS_DIR, "country_trends.csv"),  dtype=str)
    top_inv   = pd.read_csv(os.path.join(REPORTS_DIR, "top_inventors.csv"),   dtype=str)
    top_comp  = pd.read_csv(os.path.join(REPORTS_DIR, "top_companies.csv"),   dtype=str)

    for df in [patents, inventors, companies, trends, top_inv, top_comp]:
        df.columns = df.columns.str.lower().str.strip()

    patents["filing_year"] = pd.to_numeric(patents.get("filing_year", pd.Series()), errors="coerce")
    trends["year"]         = pd.to_numeric(trends["year"],     errors="coerce")
    trends["patents"]      = pd.to_numeric(trends["patents"],   errors="coerce")
    top_inv["patents"]     = pd.to_numeric(top_inv["patents"],  errors="coerce")
    top_comp["patents"]    = pd.to_numeric(top_comp["patents"], errors="coerce")

    return patents, inventors, companies, trends, top_inv, top_comp

patents, inventors, companies, trends, top_inv, top_comp = load_data()

min_year = int(patents["filing_year"].dropna().min())
max_year = int(patents["filing_year"].dropna().max())

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("📊 Patent Analytics")
st.sidebar.markdown("---")
year_range = st.sidebar.slider("📅 Year Range", min_value=min_year, max_value=max_year, value=(2010, max_year), step=1)
y1, y2 = year_range
top_n = st.sidebar.slider("🔢 Top N Results", 5, 25, 10)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Showing:** {y1} – {y2}")
st.sidebar.markdown("**Source:** USPTO Patent Database")

filtered_patents = patents[patents["filing_year"].between(y1, y2)]

# ── Title ──────────────────────────────────────────────────────────────────────
st.title("📊 Patent Analysis Dashboard")
st.markdown(f"Exploring USPTO patent data from **{y1}** to **{y2}**.")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.subheader("📌 Summary Statistics")
total_patents   = len(filtered_patents)
total_inventors = inventors["inventor_id"].nunique() if "inventor_id" in inventors.columns else len(inventors)
total_companies = companies["company_id"].nunique() if "company_id" in companies.columns else len(companies)
total_countries = inventors["country"].nunique() if "country" in inventors.columns else 0
avg_per_year    = round(total_patents / max(1, y2 - y1 + 1), 0)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📄 Patents",          f"{total_patents:,}")
k2.metric("👤 Inventors",        f"{total_inventors:,}")
k3.metric("🏢 Companies",        f"{total_companies:,}")
k4.metric("🌍 Countries",        f"{total_countries:,}")
k5.metric("📅 Avg Patents/Year", f"{avg_per_year:,.0f}")
st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Trend", "👤 Inventors", "🏢 Companies", "🌍 Countries",
    "🔍 Explorer", "🔗 Multi-Company", "🏆 Rankings"
])

# ── Tab 1: Trend ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Patent Filing Trend ({y1}–{y2})")
    df_trend = filtered_patents.groupby("filing_year").size().reset_index(name="patent_count").sort_values("filing_year")
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.area(df_trend, x="filing_year", y="patent_count",
                      labels={"filing_year": "Year", "patent_count": "Patents Filed"},
                      title="Patents Filed Per Year")
        fig.update_traces(line_color="#6366F1", fillcolor="rgba(99,102,241,0.15)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 📊 Insights")
        if len(df_trend) > 0:
            peak   = df_trend.loc[df_trend["patent_count"].idxmax()]
            low    = df_trend.loc[df_trend["patent_count"].idxmin()]
            growth = ((df_trend.iloc[-1]["patent_count"] / max(1, df_trend.iloc[0]["patent_count"])) - 1) * 100
            st.metric("Peak Year",   f"{int(peak['filing_year'])}", f"{int(peak['patent_count']):,} patents")
            st.metric("Lowest Year", f"{int(low['filing_year'])}",  f"{int(low['patent_count']):,} patents")
            st.metric("Growth",      f"{growth:+.1f}%")
    st.dataframe(df_trend, use_container_width=True, hide_index=True)

# ── Tab 2: Inventors ───────────────────────────────────────────────────────────
with tab2:
    st.subheader(f"Top {top_n} Inventors")
    df_inv = top_inv.head(top_n).copy()
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.bar(df_inv, x="patents", y="name", orientation="h",
                     labels={"patents": "Patents", "name": "Inventor"},
                     title=f"Top {top_n} Inventors")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        fig.update_traces(marker_color="#3B82F6")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 🥇 Top 5")
        for i, row in df_inv.head(5).iterrows():
            st.markdown(f"**#{i+1}** {row['name']}  \n`{int(row['patents']):,} patents`")
            st.markdown("---")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

# ── Tab 3: Companies ───────────────────────────────────────────────────────────
with tab3:
    st.subheader(f"Top {top_n} Companies")
    df_comp = top_comp.head(top_n).copy()
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_comp, x="patents", y="name", orientation="h",
                     labels={"patents": "Patents", "name": "Company"},
                     title=f"Top {top_n} Companies")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        fig.update_traces(marker_color="#10B981")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.pie(df_comp, names="name", values="patents", title="Market Share")
        st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

# ── Tab 4: Countries ───────────────────────────────────────────────────────────
with tab4:
    st.subheader(f"Top {top_n} Countries ({y1}–{y2})")
    filtered_trends = trends[trends["year"].between(y1, y2)]
    df_ctry = (filtered_trends.groupby("country")["patents"].sum()
               .reset_index().sort_values("patents", ascending=False).head(top_n))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_ctry, x="country", y="patents",
                     labels={"patents": "Patents", "country": "Country"},
                     title=f"Top {top_n} Countries")
        fig.update_traces(marker_color="#F59E0B")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.pie(df_ctry, names="country", values="patents", title="Share by Country")
        st.plotly_chart(fig2, use_container_width=True)
    top5 = df_ctry["country"].head(5).tolist()
    fig3 = px.line(filtered_trends[filtered_trends["country"].isin(top5)],
                   x="year", y="patents", color="country",
                   title="Top 5 Countries — Trend Over Time")
    st.plotly_chart(fig3, use_container_width=True)
    st.dataframe(df_ctry, use_container_width=True, hide_index=True)

# ── Tab 5: Explorer ────────────────────────────────────────────────────────────
with tab5:
    st.subheader("🔍 Patent Explorer")
    search = st.text_input("Search patent titles", placeholder="e.g. semiconductor, battery, AI...")
    df_exp = filtered_patents.copy()
    if search:
        df_exp = df_exp[df_exp["title"].str.contains(search, case=False, na=False)]
    st.markdown(f"Showing **{len(df_exp):,}** results")
    st.dataframe(df_exp.head(200), use_container_width=True, hide_index=True)

# ── Tab 6: Multi-Company ───────────────────────────────────────────────────────
with tab6:
    st.subheader("Top Inventors by Patent Volume")
    st.caption("Full multi-company analysis requires the complete database.")
    fig = px.bar(top_inv.head(top_n), x="name", y="patents",
                 title="Top Inventors by Patent Count",
                 labels={"name": "Inventor", "patents": "Patents"})
    fig.update_traces(marker_color="#8B5CF6")
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top_inv.head(top_n), use_container_width=True, hide_index=True)

# ── Tab 7: Rankings ────────────────────────────────────────────────────────────
with tab7:
    st.subheader("Inventor Rankings")
    df_rank = top_inv.head(top_n).copy()
    df_rank.insert(0, "world_rank", range(1, len(df_rank) + 1))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🌐 World Rankings")
        st.dataframe(df_rank[["world_rank", "name", "patents"]], use_container_width=True, hide_index=True)
    with col2:
        fig = px.bar(df_rank, x="name", y="patents", text="world_rank",
                     labels={"name": "Inventor", "patents": "Patents"},
                     title="Top Inventors Ranked")
        fig.update_traces(textposition="outside", marker_color="#6366F1")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption(f"Patent Analysis Dashboard · {y1}–{y2} · Streamlit & Plotly · USPTO Data")
