import streamlit as st
from typing import Optional

# External modules (you must implement these)
from auth import login_user
from db import fetch_data

import io
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import pandas as pd
import streamlit as st


# ---------------------------
# Page Configuration
# ---------------------------
st.set_page_config(
    page_title="Logistics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# Session State Initialization
# ---------------------------
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None


# ---------------------------
# Login Logic
# ---------------------------
def login(username: str, password: str) -> bool:
    result = login_user(username, password)

    if result["success"]:
        st.session_state.authenticated = True
        st.session_state.username = result["user"]["username"]
        return True
    else:
        st.error(result["message"])
        return False


def logout():
    """
    Logout user and clear session
    """
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


# ---------------------------
# UI Components
# ---------------------------
def login_page():
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.warning("Please enter both username and password.")
                return

            if login(username, password):
                st.success("Login successful!")
                st.session_state.username = username
                st.rerun()



# ---------------------------
# Theme / Styling
# ---------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(128,128,128,0.18);
    padding: 0.9rem 1rem;
    border-radius: 14px;
}
.small-muted {
    color: #6b7280;
    font-size: 0.9rem;
}
.filter-card {
    padding: 0.9rem 1rem 0.2rem 1rem;
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 14px;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------
# Helpers
# ---------------------------
def safe_div(a, b):
    if b is None or pd.isna(b) or b == 0:
        return np.nan
    return a / b

def fmt_currency(v, decimals=0):
    return "-" if pd.isna(v) else f"${v:,.{decimals}f}"

def fmt_number(v, decimals=0):
    return "-" if pd.isna(v) else f"{v:,.{decimals}f}"

def fmt_pct(v, decimals=1):
    return "-" if pd.isna(v) else f"{v:.{decimals}f}%"

def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


# ---------------------------
# Data Loader
# ---------------------------
@st.cache_data(show_spinner=False)
def load_data():
    data = fetch_data()
    df = pd.DataFrame(data)

    if df.empty:
        return df

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Datetime parsing
    for col in ["pickup_datetime", "delivery_datetime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Numeric coercion
    numeric_cols = ["loadboard_rate", "miles", "weight"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # String cleanup
    string_cols = ["origin", "destination", "equipment_type"]
    for col in string_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            )

    # Derived fields
    if {"origin", "destination"}.issubset(df.columns):
        df["route"] = df["origin"].fillna("Unknown") + " → " + df["destination"].fillna("Unknown")

    if {"loadboard_rate", "miles"}.issubset(df.columns):
        df["rate_per_mile"] = np.where(df["miles"] > 0, df["loadboard_rate"] / df["miles"], np.nan)

    if {"pickup_datetime", "delivery_datetime"}.issubset(df.columns):
        transit = df["delivery_datetime"] - df["pickup_datetime"]
        df["transit_hours"] = transit.dt.total_seconds() / 3600
        df["transit_days"] = df["transit_hours"] / 24

    if "pickup_datetime" in df.columns:
        df["pickup_date"] = df["pickup_datetime"].dt.date
        df["pickup_day"] = df["pickup_datetime"].dt.day_name()
        df["pickup_week"] = df["pickup_datetime"].dt.to_period("W").dt.start_time
        df["pickup_month"] = df["pickup_datetime"].dt.to_period("M").dt.start_time

    return df


# ---------------------------
# KPI Delta Logic
# ---------------------------
def calculate_period_delta(df, date_col, value_col=None, agg="count"):
    if df.empty or date_col not in df.columns:
        return np.nan, []

    temp = df.dropna(subset=[date_col]).copy()
    if temp.empty:
        return np.nan, []
    
    temp['date_only'] = pd.to_datetime(temp[date_col]).dt.date
    
    max_date = temp['date_only'].max()
    min_date = temp['date_only'].min()
    
    total_days = (max_date - min_date).days
    
    window_days = min(7, total_days)
    current_start = max_date - pd.Timedelta(days=window_days)
    prev_start = current_start - pd.Timedelta(days=window_days)
    
    # Use date_only for bucketing
    current = temp[temp['date_only'] > current_start]
    previous = temp[(temp['date_only'] > prev_start) & 
                   (temp['date_only'] <= current_start)]

    if agg == "count":
        cur_val = len(current)
        prev_val = len(previous)
        series = temp.set_index(date_col).resample("D").size().tail(14).tolist()
    else:
        current = current.dropna(subset=[value_col])
        previous = previous.dropna(subset=[value_col])

        if agg == "mean":
            cur_val = current[value_col].mean()
            prev_val = previous[value_col].mean()
            series = temp.set_index(date_col)[value_col].resample("D").mean().fillna(0).tail(14).tolist()
        elif agg == "sum":
            cur_val = current[value_col].sum()
            prev_val = previous[value_col].sum()
            series = temp.set_index(date_col)[value_col].resample("D").sum().fillna(0).tail(14).tolist()
        else:
            return np.nan, []

    if pd.isna(prev_val) or prev_val == 0:
        delta_pct = np.nan
    else:
        delta_pct = ((cur_val - prev_val) / prev_val) * 100

    return delta_pct, series


# ---------------------------
# Main Dashboard
# ---------------------------
def dashboard_page():
    st.title("📊 Logistics Dashboard")

    df = load_data()

    if df.empty:
        st.warning("No data available.")
        return

    last_updated = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    st.caption(f"Updated {last_updated}")
    if "reset_filters_flag" not in st.session_state:
        st.session_state.reset_filters_flag = False

    if st.session_state.reset_filters_flag:
        st.session_state.origin_filter = []
        st.session_state.destination_filter = []
        st.session_state.equipment_filter = []
        st.session_state.complete_only = False

        if "pickup_datetime" in df.columns and df["pickup_datetime"].notna().any():
            st.session_state.date_range = (
                df["pickup_datetime"].min().date(),
                df["pickup_datetime"].max().date(),
            )

        if "miles" in df.columns and df["miles"].notna().any():
            st.session_state.miles_range = (
                float(df["miles"].min()),
                float(df["miles"].max()),
            )

        if "loadboard_rate" in df.columns and df["loadboard_rate"].notna().any():
            st.session_state.rate_range = (
                float(df["loadboard_rate"].min()),
                float(df["loadboard_rate"].max()),
            )

        st.session_state.reset_filters_flag = False

        # ---------------------------
    # Filter Bar
    # ---------------------------
    with st.container():
        st.subheader("Filters")

        f1, f2, f3, f4 = st.columns(4)

        with f1:
            origin_filter = st.multiselect(
                "Origin",
                options=sorted(df["origin"].dropna().unique().tolist()) if "origin" in df.columns else [],
                key="origin_filter",
            )

        with f2:
            destination_filter = st.multiselect(
                "Destination",
                options=sorted(df["destination"].dropna().unique().tolist()) if "destination" in df.columns else [],
                key="destination_filter",
            )

        with f3:
            equipment_filter = st.multiselect(
                "Equipment Type",
                options=sorted(df["equipment_type"].dropna().unique().tolist()) if "equipment_type" in df.columns else [],
                key="equipment_filter",
            )

        with f4:
            if "pickup_datetime" in df.columns and df["pickup_datetime"].notna().any():
                min_dt = df["pickup_datetime"].min().date()
                max_dt = df["pickup_datetime"].max().date()

                if "date_range" not in st.session_state:
                    st.session_state.date_range = (min_dt, max_dt)

                date_range = st.date_input(
                    "Pickup Date Range",
                    key="date_range",
                )
            else:
                date_range = None

        d1, d2 = st.columns(2)

        with d1:
            if "miles" in df.columns and df["miles"].notna().any():
                miles_min = float(df["miles"].min())
                miles_max = float(df["miles"].max())

                if "miles_range" not in st.session_state:
                    st.session_state.miles_range = (miles_min, miles_max)

                miles_range = st.slider(
                    "Miles Range",
                    min_value=miles_min,
                    max_value=miles_max,
                    key="miles_range",
                )
            else:
                miles_range = None

        with d2:
            if "loadboard_rate" in df.columns and df["loadboard_rate"].notna().any():
                rate_min = float(df["loadboard_rate"].min())
                rate_max = float(df["loadboard_rate"].max())

                if "rate_range" not in st.session_state:
                    st.session_state.rate_range = (rate_min, rate_max)

                rate_range = st.slider(
                    "Rate Range",
                    min_value=rate_min,
                    max_value=rate_max,
                    key="rate_range",
                )
            else:
                rate_range = None
    if st.button("Reset filters"):
        st.session_state.reset_filters_flag = True
        st.rerun()


        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------
    # Apply Filters
    # ---------------------------
    filtered_df = df.copy()

    if origin_filter:
        filtered_df = filtered_df[filtered_df["origin"].isin(origin_filter)]

    if destination_filter:
        filtered_df = filtered_df[filtered_df["destination"].isin(destination_filter)]

    if equipment_filter:
        filtered_df = filtered_df[filtered_df["equipment_type"].isin(equipment_filter)]

    if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and "pickup_datetime" in filtered_df.columns:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered_df = filtered_df[
            filtered_df["pickup_datetime"].between(start_date, end_date, inclusive="both")
        ]

    if miles_range and "miles" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["miles"].between(miles_range[0], miles_range[1], inclusive="both")]

    if rate_range and "loadboard_rate" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["loadboard_rate"].between(rate_range[0], rate_range[1], inclusive="both")
        ]


    if filtered_df.empty:
        st.warning("No rows match the selected filters.")
        return
    # ---------------------------
    # KPIs
    # ---------------------------
    total_loads = len(filtered_df)
    avg_rate = filtered_df["loadboard_rate"].mean() if "loadboard_rate" in filtered_df.columns else np.nan
    total_miles = filtered_df["miles"].sum() if "miles" in filtered_df.columns else np.nan
    avg_weight = filtered_df["weight"].mean() if "weight" in filtered_df.columns else np.nan
    avg_rpm = filtered_df["rate_per_mile"].mean() if "rate_per_mile" in filtered_df.columns else np.nan
    avg_transit_days = filtered_df["transit_days"].mean() if "transit_days" in filtered_df.columns else np.nan

    loads_delta, loads_spark = calculate_period_delta(filtered_df, "pickup_datetime", agg="count") if "pickup_datetime" in filtered_df.columns else (np.nan, [])
    rate_delta, rate_spark = calculate_period_delta(filtered_df, "pickup_datetime", value_col="loadboard_rate", agg="mean") if {"pickup_datetime", "loadboard_rate"}.issubset(filtered_df.columns) else (np.nan, [])
    miles_delta, miles_spark = calculate_period_delta(filtered_df, "pickup_datetime", value_col="miles", agg="sum") if {"pickup_datetime", "miles"}.issubset(filtered_df.columns) else (np.nan, [])
    weight_delta, weight_spark = calculate_period_delta(filtered_df, "pickup_datetime", value_col="weight", agg="mean") if {"pickup_datetime", "weight"}.issubset(filtered_df.columns) else (np.nan, [])
    rpm_delta, rpm_spark = calculate_period_delta(filtered_df, "pickup_datetime", value_col="rate_per_mile", agg="mean") if {"pickup_datetime", "rate_per_mile"}.issubset(filtered_df.columns) else (np.nan, [])
    transit_delta, transit_spark = calculate_period_delta(filtered_df, "pickup_datetime", value_col="transit_days", agg="mean") if {"pickup_datetime", "transit_days"}.issubset(filtered_df.columns) else (np.nan, [])

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    k1.metric(
        "Total Loads",
        f"{total_loads:,}",
        delta=None if pd.isna(loads_delta) else f"{loads_delta:+.1f}% vs prev",
        chart_data=loads_spark if loads_spark else None,
        chart_type="area",
    )
    k2.metric(
        "Avg Rate",
        fmt_currency(avg_rate, 2),
        delta=None if pd.isna(rate_delta) else f"{rate_delta:+.1f}% vs prev",
        chart_data=rate_spark if rate_spark else None,
        chart_type="line",
    )
    k3.metric(
        "Total Miles",
        fmt_number(total_miles, 0),
        delta=None if pd.isna(miles_delta) else f"{miles_delta:+.1f}% vs prev",
        chart_data=miles_spark if miles_spark else None,
        chart_type="bar",
    )
    k4.metric(
        "Avg Weight",
        fmt_number(avg_weight, 0),
        delta=None if pd.isna(weight_delta) else f"{weight_delta:+.1f}% vs prev",
        chart_data=weight_spark if weight_spark else None,
        chart_type="line",
    )
    k5.metric(
        "Rate / Mile",
        fmt_currency(avg_rpm, 2),
        delta=None if pd.isna(rpm_delta) else f"{rpm_delta:+.1f}% vs prev",
        chart_data=rpm_spark if rpm_spark else None,
        chart_type="line",
    )
    k6.metric(
        "Transit Days",
        fmt_number(avg_transit_days, 1),
        delta=None if pd.isna(transit_delta) else f"{transit_delta:+.1f}% vs prev",
        chart_data=transit_spark if transit_spark else None,
        chart_type="line",
    )

    st.divider()

    # ---------------------------
    # Chart Controls
    # ---------------------------
    c1, c2 = st.columns([1, 1])
    with c1:
        time_grain = st.segmented_control(
            "Time Grain",
            options=["Day", "Week", "Month"],
            default="Day",
        )
    with c2:
        top_n = st.selectbox("Top Routes", options=[5, 10, 15, 20], index=1)

    # ---------------------------
    # Charts Row 1
    # ---------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Loads Over Time")

        time_df = filtered_df.dropna(subset=["pickup_datetime"]).copy()
        if not time_df.empty:
            if time_grain == "Day":
                series = time_df.set_index("pickup_datetime").resample("D").size().reset_index(name="loads")
            elif time_grain == "Week":
                series = time_df.set_index("pickup_datetime").resample("W").size().reset_index(name="loads")
            else:
                series = time_df.set_index("pickup_datetime").resample("MS").size().reset_index(name="loads")

            fig = px.line(
                series,
                x="pickup_datetime",
                y="loads",
                markers=True,
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title=None,
                yaxis_title="Loads",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pickup timestamps available for trend analysis.")

    with col2:
        st.subheader("Rate Distribution")

        rate_df = filtered_df.dropna(subset=["loadboard_rate"]).copy()
        if not rate_df.empty:
            fig = px.histogram(
                rate_df,
                x="loadboard_rate",
                nbins=30,
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Loadboard Rate ($)",
                yaxis_title="Loads",
                bargap=0.05,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rate data available.")

    # ---------------------------
    # Charts Row 2
    # ---------------------------
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Top Routes")

        if {"origin", "destination"}.issubset(filtered_df.columns):
            routes = (
                filtered_df.groupby(["origin", "destination"], dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values(by="count", ascending=False)
                .head(top_n)
            )
            routes["route"] = routes["origin"].fillna("Unknown") + " → " + routes["destination"].fillna("Unknown")

            fig = px.bar(
                routes.sort_values("count", ascending=True),
                x="count",
                y="route",
                orientation="h",
                text="count",
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Loads",
                yaxis_title=None,
                showlegend=False,
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Origin/destination columns not available.")

    with col4:
        st.subheader("Equipment Usage")

        if "equipment_type" in filtered_df.columns and filtered_df["equipment_type"].notna().any():
            equipment_counts = (
                filtered_df["equipment_type"]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )
            equipment_counts.columns = ["equipment_type", "count"]

            fig = px.pie(
                equipment_counts,
                names="equipment_type",
                values="count",
                hole=0.52,
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No equipment data available.")

    # ---------------------------
    # Charts Row 3
    # ---------------------------
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Miles vs Rate")

        needed = {"miles", "loadboard_rate"}
        scatter_df = filtered_df.dropna(subset=list(needed)).copy() if needed.issubset(filtered_df.columns) else pd.DataFrame()

        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x="miles",
                y="loadboard_rate",
                color="equipment_type" if "equipment_type" in scatter_df.columns else None,
                hover_data=["origin", "destination", "weight"] if {"origin", "destination", "weight"}.issubset(scatter_df.columns) else None,
                template="plotly_white",
                opacity=0.75,
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Miles",
                yaxis_title="Rate ($)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Miles and rate are required for scatter analysis.")

    with col6:
        st.subheader("Pickup Weekday Pattern")

        if "pickup_day" in filtered_df.columns and filtered_df["pickup_day"].notna().any():
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_df = (
                filtered_df["pickup_day"]
                .value_counts()
                .reindex(weekday_order, fill_value=0)
                .reset_index()
            )
            weekday_df.columns = ["pickup_day", "count"]

            fig = px.bar(
                weekday_df,
                x="pickup_day",
                y="count",
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title=None,
                yaxis_title="Loads",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pickup datetime data available.")

    st.divider()

    # ---------------------------
    # Details / Export
    # ---------------------------
    st.subheader("Load Details")

    display_df = filtered_df.copy()

    preferred_cols = [
        "pickup_datetime", "delivery_datetime", "origin", "destination", "route",
        "equipment_type", "miles", "weight", "loadboard_rate", "rate_per_mile", "transit_days"
    ]
    available_cols = [c for c in preferred_cols if c in display_df.columns]
    extra_cols = [c for c in display_df.columns if c not in available_cols]

    selected_cols = st.multiselect(
        "Visible columns",
        options=available_cols + extra_cols,
        default=available_cols if available_cols else display_df.columns.tolist()[:8],
    )

    if selected_cols:
        display_df = display_df[selected_cols]

    sort_col = "pickup_datetime" if "pickup_datetime" in display_df.columns else display_df.columns[0]
    display_df = display_df.sort_values(by=sort_col, ascending=False, na_position="last")

    st.download_button(
        "Download filtered CSV",
        data=to_csv_bytes(display_df),
        file_name="logistics_dashboard_filtered.csv",
        mime="text/csv",
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=460,
        hide_index=True,
        column_config={
            "pickup_datetime": st.column_config.DatetimeColumn("Pickup", format="YYYY-MM-DD HH:mm"),
            "delivery_datetime": st.column_config.DatetimeColumn("Delivery", format="YYYY-MM-DD HH:mm"),
            "loadboard_rate": st.column_config.NumberColumn("Rate ($)", format="$%.2f"),
            "rate_per_mile": st.column_config.NumberColumn("Rate/Mile", format="$%.2f"),
            "miles": st.column_config.NumberColumn("Miles", format="%.0f"),
            "weight": st.column_config.NumberColumn("Weight", format="%.0f"),
            "transit_days": st.column_config.NumberColumn("Transit Days", format="%.1f"),
        }
    )

    st.divider()

    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("Logout", use_container_width=True):
            logout()
    with c2:
        st.markdown('<div class="small-muted">Showing filtered operational data with derived logistics metrics.</div>', unsafe_allow_html=True)



# ---------------------------
# Main App Router
# ---------------------------
def main():
    init_session_state()

    if st.session_state.authenticated:
        dashboard_page()
    else:
        login_page()


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    main()