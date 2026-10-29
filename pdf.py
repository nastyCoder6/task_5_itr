import io

import vl_convert as vlc
from fpdf import FPDF


def build_pdf_report(summary_df, outliers_df, chart, anomaly_test, metric):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.cell(
        0,
        10,
        "Weyland-Yutani Extraction Report",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Overview", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 10)

    summary_df = summary_df.reset_index()
    col_width = 190 / len(summary_df.columns)

    for col_name in summary_df.columns:
        pdf.cell(col_width, 8, str(col_name), border=1, align="C")
    pdf.ln()

    for _, row in summary_df.iterrows():
        for col_name in summary_df.columns:
            val = row[col_name]
            val_str = f"{val}"
            pdf.cell(col_width, 8, val_str, border=1, align="C")
        pdf.ln()
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(
        0,
        10,
        f"2. Anomaly Detection ({len(outliers_df)} found)",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("helvetica", "I", 10)

    pdf.cell(
        0,
        10,
        f"Based on {anomaly_test} test with detection parameter(s) set to {metric}.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    if outliers_df.empty:
        pdf.set_font("helvetica", "", 10)
        pdf.cell(
            0,
            10,
            "No anomalies detected.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
    else:
        for _, row in outliers_df.iterrows():
            mine = row["Mine"]
            date_str = str(row["Date"]).split()[0]
            production = row["Production"]

            pdf.set_font("helvetica", "B", 10)
            pdf.cell(
                0,
                8,
                f"Alert: {mine} on {date_str}",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font("helvetica", "", 10)
            description = (
                f"Deviation was recorded at the {mine} facility on {date_str}. "
                f"Production reached {production:.2f} (t)."
            )
            pdf.multi_cell(0, 6, description)
            pdf.ln(2)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "3. Operations Chart", new_x="LMARGIN", new_y="NEXT")

    export_chart = chart.properties(width=800, height=400)

    chart_dict = export_chart.to_dict()

    chart_png_bytes = vlc.vegalite_to_png(vl_spec=chart_dict, scale=2.0)

    chart_io = io.BytesIO(chart_png_bytes)

    pdf.image(chart_io, w=190)

    return bytes(pdf.output())
