import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analyzer import DataAnalyzer
from cleaner import DataCleaner
from loader import DataLoader
from pdf import build_pdf_report

raw_df = DataLoader().load_data()
df = DataCleaner(raw_df).get_clean_df()
analyzer = DataAnalyzer(df)


st.set_page_config("TASK 5", page_icon="🦈", layout="wide")
st.title("Weyland-Yutani Operations Analysis")

st.subheader("1. Overview (t)")
summary_df = analyzer.get_summary_table()
st.dataframe(summary_df, width="content")


st.subheader("2. Anomaly Detection")

anomaly_test = st.selectbox(
    "Select Anomaly Detection Method:",
    ["IQR Rule", "Z-Score", "Moving Average Distance (%)", "Grubbs' Test"],
)

if anomaly_test == "IQR Rule":
    multiplier = st.slider(
        "IQR Multiplier:", min_value=0.5, max_value=3.0, value=1.5, step=0.1
    )
    outliers_df = analyzer.get_anomalies_iqr(multiplier=multiplier)
    metric = multiplier
elif anomaly_test == "Z-Score":
    threshold = st.slider(
        "Z-Score Threshold:", min_value=1.0, max_value=4.0, value=2.5, step=0.1
    )
    outliers_df = analyzer.get_anomalies_zscore(threshold=threshold)
    metric = threshold

elif anomaly_test == "Moving Average Distance (%)":
    col_a, col_b = st.columns(2)
    with col_a:
        window = st.number_input(
            "Moving Average Window (Days):", min_value=2, max_value=30, value=7, step=1
        )
    with col_b:
        pct = st.slider(
            "Distance Threshold (%):", min_value=5, max_value=100, value=25, step=5
        )
    outliers_df = analyzer.get_anomalies_ma(window=window, threshold_pct=pct / 100.0)
    metric = [window, pct]

elif anomaly_test == "Grubbs' Test":
    alpha = st.slider(
        "Significance Level (Alpha):",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
    )
    outliers_df = analyzer.get_anomalies_grubbs(alpha=alpha)
    metric = alpha

with st.expander(f"View Detected Anomalies ({len(outliers_df)} found)", expanded=True):
    if outliers_df.empty:
        st.info("No anomalies detected with the current parameters.")
    else:
        st.dataframe(
            outliers_df.sort_values(["Mine", "Date"]),
            width="content",
            hide_index=True,
        )


st.subheader("3. Operations Chart")

col1, col2, col3 = st.columns(3)

with col1:
    chart_type = st.selectbox("Select Chart Type:", ["line", "bar", "stacked"])

with col2:
    trend_choice = st.selectbox("Polynomial Trendline Degree:", ["None", 1, 2, 3, 4])
    trend_deg = None if trend_choice == "None" else int(trend_choice)

with col3:
    all_series = list(df["Mine"].unique())
    default_series = (
        [m for m in all_series if m != "Total"]
        if chart_type == "stacked"
        else all_series
    )
    selected_series = st.multiselect(
        "Displayed Series:", options=all_series, default=default_series
    )

plot_df = df[df["Mine"].isin(selected_series)].copy()
plot_outliers = outliers_df[outliers_df["Mine"].isin(selected_series)].copy()

if not plot_df.empty:
    base = alt.Chart(plot_df).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Production:Q", title="Daily Output (t)"),
        color=alt.Color("Mine:N", title="Mine"),
    )

    if chart_type == "line":
        main_layer = base.mark_line()
    elif chart_type == "bar":
        main_layer = base.mark_bar().encode(xOffset="Mine:N")
    elif chart_type == "stacked":
        main_layer = base.mark_bar()

    layers = [main_layer]

    if not plot_outliers.empty:
        outlier_layer = (
            alt.Chart(plot_outliers)
            .mark_point(color="red", size=120, shape="cross", filled=True, opacity=1.0)
            .encode(
                x="Date:T",
                y="Production:Q",
                tooltip=["Date:T", "Mine:N", "Production:Q"],
            )
        )
        layers.append(outlier_layer)

    if trend_deg in [1, 2, 3, 4]:
        trend_records = []
        for mine, group in plot_df.groupby("Mine"):
            group = group.sort_values("Date")
            if len(group) > trend_deg:
                x_idx = np.arange(len(group))
                coeffs = np.polyfit(x_idx, group["Production"], trend_deg)
                y_fit = np.polyval(coeffs, x_idx)
                for d, y_val in zip(group["Date"], y_fit):
                    trend_records.append({"Date": d, "Mine": mine, "Trend": y_val})

        if trend_records:
            trend_df = pd.DataFrame(trend_records)
            trend_layer = (
                alt.Chart(trend_df)
                .mark_line(strokeDash=[6, 4], strokeWidth=2)
                .encode(x="Date:T", y="Trend:Q", color="Mine:N")
            )
            layers.append(trend_layer)

    final_chart = alt.layer(*layers).interactive()
    st.altair_chart(final_chart, width="content")
else:
    st.warning("Please select at least one mine to display the chart.")


st.divider()

st.subheader("Export")
st.markdown("Generate and download a PDF version of current dashboard.")


if st.button("Generate", type="primary"):
    pdf_data = build_pdf_report(
        summary_df, outliers_df, final_chart, anomaly_test, metric
    )

    st.download_button(
        label="Download",
        data=pdf_data,
        file_name="WY_Extraction_Report.pdf",
        mime="application/pdf",
    )
