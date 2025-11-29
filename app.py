import pandas as pd
import streamlit as st

from src.config import PROCESSED_DATA_PATH
from src.insights import generate_company_insight

st.set_page_config(
    page_title="AI Market Intelligence Platform",
    layout="wide",
)


@st.cache_data
def load_processed_data():
    return pd.read_parquet(PROCESSED_DATA_PATH)


def main():
    st.title("📊 AI-Driven Market Intelligence & Opportunity Discovery")

    st.markdown(
        """
        This dashboard analyzes Indian startup funding data to identify **market segments**, 
        **growth potential**, and **unusual (potentially high-opportunity or high-risk) startups**.
        """
    )

    # ---------- LOAD DATA ----------
    df = load_processed_data()

    # ---------- SIDEBAR FILTERS ----------
    st.sidebar.header("Filters")
    locations = ["All"] + sorted(df["Location"].dropna().unique().tolist())
    sectors = ["All"] + sorted(df["Sector"].dropna().unique().tolist())
    stages = ["All"] + sorted(df["Stage"].dropna().unique().tolist())

    selected_location = st.sidebar.selectbox("Location", locations)
    selected_sector = st.sidebar.selectbox("Sector", sectors)
    selected_stage = st.sidebar.selectbox("Stage", stages)
    show_anomalies_only = st.sidebar.checkbox(
        "Show anomalies only (unusual startups)", value=False
    )

    # ---------- APPLY FILTERS ----------
    filtered_df = df.copy()
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_location]
    if selected_sector != "All":
        filtered_df = filtered_df[filtered_df["Sector"] == selected_sector]
    if selected_stage != "All":
        filtered_df = filtered_df[filtered_df["Stage"] == selected_stage]
    if show_anomalies_only:
        filtered_df = filtered_df[filtered_df["is_anomaly"] == True]

    # ---------- SEGMENT OVERVIEW ----------
    st.subheader("Segment Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Startups (filtered)", len(filtered_df))
    with col2:
        avg_funding = filtered_df["Amount"].mean() if not filtered_df.empty else 0
        st.metric("Avg Funding (₹)", f"{avg_funding:,.0f}")
    with col3:
        anomaly_rate = (
            (filtered_df["is_anomaly"].mean() * 100) if not filtered_df.empty else 0
        )
        st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")

    # ---------- CLUSTER DISTRIBUTION ----------
    st.write("### Cluster Distribution")
    if not filtered_df.empty:
        cluster_counts = filtered_df["cluster_label"].value_counts().reset_index()
        cluster_counts.columns = ["Cluster", "Count"]
        st.bar_chart(cluster_counts.set_index("Cluster"))
    else:
        st.write("No data for the selected filters.")

    # ---------- AVERAGE FUNDING BY CLUSTER ----------
    st.write("### Average Funding by Cluster")
    if not filtered_df.empty:
        cluster_summary = (
            filtered_df.groupby("cluster_label")["Amount"]
            .mean()
            .reset_index()
            .rename(columns={"Amount": "avg_funding"})
        )
        st.dataframe(cluster_summary)
    else:
        st.write("No cluster data for current filters.")

    # ---------- TOP SECTORS BY TOTAL FUNDING ----------
    st.write("### Top Sectors by Total Funding")
    if not filtered_df.empty:
        sector_summary = (
            filtered_df.groupby("Sector")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
        )
        top_k = min(10, len(sector_summary))
        sector_summary_top = sector_summary.head(top_k)
        st.bar_chart(
            sector_summary_top.set_index("Sector")["Amount"]
        )
    else:
        st.write("No sector data for current filters.")

    # ---------- TOP STARTUPS BY FUNDING ----------
    st.write("### Top Startups by Funding")
    if not filtered_df.empty:
        top_n = st.slider("Number of startups to display", 3, 20, 10)
        top_companies = (
            filtered_df.sort_values("Amount", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        st.dataframe(
            top_companies[
                [
                    "Company Name",
                    "Location",
                    "Sector",
                    "Stage",
                    "cluster_label",
                    "Amount",
                    "company_age",
                    "is_anomaly",
                ]
            ]
        )

        # ---------- AI-GENERATED INSIGHT ----------
        st.write("### AI-Generated Insight")
        company_options = top_companies["Company Name"].tolist()
        selected_company = st.selectbox("Select a startup", company_options)
        selected_row = top_companies[
            top_companies["Company Name"] == selected_company
        ].iloc[0]
        insight_text = generate_company_insight(selected_row)
        st.info(insight_text)
    else:
        st.info("No startups matching the current filters.")

    # ---------- FUNDING VS COMPANY AGE ----------
    st.write("### Funding vs Company Age (Filtered Data)")
    if not filtered_df.empty:
        st.scatter_chart(
            filtered_df,
            x="company_age",
            y="Amount",
            color="cluster_label",
        )

    # ---------- DOWNLOAD FILTERED DATA ----------
    st.write("### Download filtered dataset")
    if not filtered_df.empty:
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name="filtered_startups.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
