import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="DS Jobs — Mini Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      /* header {visibility: hidden;} */ 
      .block-container {padding-top: 1.2rem; padding-bottom: 1.2rem;}
      .kpi-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 14px 14px 12px;
      }
      .kpi-label {color: rgba(255,255,255,0.68); font-size: 0.85rem; margin: 0;}
      .kpi-value {font-size: 1.55rem; font-weight: 800; margin: 0.25rem 0 0;}
      .hero {
        background: linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03));
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 22px;
        padding: 16px 16px 12px;
        margin-bottom: 12px;
      }
      .muted {color: rgba(255,255,255,0.68);}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_csv() -> pd.DataFrame:
    candidates = [
        "Data Science Jobs Salaries.csv",
        "data_science_jobs_salaries.csv",
    ]
    for c in candidates:
        if os.path.exists(c):
            return pd.read_csv(c)

    sandbox = "/mnt/data/Data Science Jobs Salaries.csv"
    if os.path.exists(sandbox):
        return pd.read_csv(sandbox)

    raise FileNotFoundError("Place 'Data Science Jobs Salaries.csv' next to this script.")

raw = load_csv()
df = raw.copy()

df["work_year"] = pd.to_numeric(
    df["work_year"].astype(str).str.extract(r"(\d{4})", expand=False),
    errors="coerce",
).astype("Int64")

df = df.dropna(subset=["work_year"])
df["work_year"] = df["work_year"].astype(int)

EXP_MAP = {"EN": "Entry", "MI": "Mid", "SE": "Senior", "EX": "Exec"}
REMOTE_MAP = {0: "On-site", 50: "Hybrid", 100: "Remote"}

df["exp"] = df["experience_level"].map(EXP_MAP).fillna(df["experience_level"])
df["remote"] = df["remote_ratio"].map(REMOTE_MAP).fillna(df["remote_ratio"].astype(str))
df["salary_in_usd"] = pd.to_numeric(df["salary_in_usd"], errors="coerce")
df = df.dropna(subset=["salary_in_usd"])

years = sorted(df["work_year"].dropna().astype(int).unique().tolist())
st.markdown(
    f"""
    <div class="hero">
      <div style="font-size:1.35rem; font-weight:850; letter-spacing:-0.02em;">Data Science Jobs — Mini Salary Dashboard</div>
      <div class="muted" style="font-size:0.9rem; margin-top:4px;">
        {len(df):,} rows • Years {min(years)}–{max(years)} • Top controls • No sidebar
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
with c1:
    year = st.selectbox("Year", options=["All"] + years, index=0)
with c2:
    exp = st.selectbox("Experience", options=["All", "Entry", "Mid", "Senior", "Exec"], index=0)
with c3:
    remote = st.selectbox("Remote", options=["All", "On-site", "Hybrid", "Remote"], index=0)
with c4:
    top_n = st.selectbox("Top N titles", options=[8, 10, 12, 15], index=2)

fdf = df.copy()
if year != "All":
    fdf = fdf[fdf["work_year"] == int(year)]
if exp != "All":
    fdf = fdf[fdf["exp"] == exp]
if remote != "All":
    fdf = fdf[fdf["remote"] == remote]

def fmt_money(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"${x:,.0f}"

k1, k2, k3, k4 = st.columns(4)
rows = len(fdf)
med = float(fdf["salary_in_usd"].median()) if rows else np.nan
avg = float(fdf["salary_in_usd"].mean()) if rows else np.nan
remote_share = (100.0 * (fdf["remote_ratio"] == 100).mean()) if rows else np.nan

def kpi(col, label, value):
    col.markdown(
        f"""
        <div class="kpi-card">
          <p class="kpi-label">{label}</p>
          <p class="kpi-value">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

kpi(k1, "Rows (filtered)", f"{rows:,}")
kpi(k2, "Median salary (USD)", fmt_money(med))
kpi(k3, "Average salary (USD)", fmt_money(avg))
kpi(k4, "Remote (100%) share", "—" if np.isnan(remote_share) else f"{remote_share:.1f}%")

if rows == 0:
    st.warning("No rows match your filters.")
    st.stop()

g1, g2 = st.columns([1.2, 1])
with g1:
    fig = px.histogram(
        fdf, x="salary_in_usd", nbins=30,
        labels={"salary_in_usd": "Salary (USD)"},
        hover_data=["job_title", "exp", "remote", "company_location"],
    )
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

with g2:
    fig2 = px.box(
        fdf, x="exp", y="salary_in_usd",
        points="outliers",
        labels={"exp": "Experience", "salary_in_usd": "Salary (USD)"},
        category_orders={"exp": ["Entry", "Mid", "Senior", "Exec"]},
    )
    fig2.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig2, use_container_width=True)

g3, g4 = st.columns(2)
with g3:
   
    top_titles = (
        fdf["job_title"]
        .value_counts()
        .head(int(top_n))
        .rename_axis("job_title")
        .reset_index(name="count")
    )

    fig3 = px.bar(
        top_titles, x="count", y="job_title", orientation="h",
        labels={"count": "Count", "job_title": "Job title"}
    )
    fig3.update_layout(margin=dict(l=10, r=10, t=20, b=10), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

with g4:
    fig4 = px.strip(
        fdf, x="remote", y="salary_in_usd",
        color="exp",
        hover_data=["job_title", "company_location"],
        labels={"remote": "Remote ratio", "salary_in_usd": "Salary (USD)", "exp": "Experience"},
        category_orders={"remote": ["On-site", "Hybrid", "Remote"], "exp": ["Entry", "Mid", "Senior", "Exec"]},
    )
    fig4.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig4, use_container_width=True)

with st.expander("Data (filtered)", expanded=False):
    st.dataframe(fdf, use_container_width=True, height=320)
    st.download_button(
        "Download filtered CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_ds_jobs.csv",
        mime="text/csv",
    )

st.caption("Embed tip: host this Streamlit app and embed it with an iframe using ?embed=true on Streamlit Community Cloud.")
