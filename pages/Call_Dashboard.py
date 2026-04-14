
import requests
import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

HAPPYROBOT_TOKEN = os.getenv("HAPPYROBOT_TOKEN")
HAPPYROBOT_WORKFLOW_ID = os.getenv("HAPPYROBOT_WORKFLOW_ID")


st.set_page_config(
    page_title="Call Dashboard",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------
# Auth guard
# ---------------------------
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.stop()

# ---------------------------
# Helpers
# ---------------------------
def fmt_currency(v, decimals=0):
    return "-" if pd.isna(v) else f"${v:,.{decimals}f}"

def fmt_number(v, decimals=0):
    return "-" if pd.isna(v) else f"{v:,.{decimals}f}"

def fetch_happyrobot_runs(workflow_id: str, token: str, page: int = 1, page_size: int = 100):
    url = f"https://platform.happyrobot.ai/api/v2/workflows/{workflow_id}/runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    params = {
        "page": page,
        "page_size": page_size,
        "sort": "desc",
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def safe_json_loads(value, default):
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default
FIELD_MAP = {
    "classification": "019d87bc-8c96-7468-ad2c-81bbfd08bd17.response.classification",
    "reasoning": "019d87ca-c77f-78f4-9327-a66ea5dec790.response.reasoning",
    "negotiation_flow": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.negotiation_flow",
    "tool_usage": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.tool_usage",
    "key_insights": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.key_insights",
    "transcript": "019d86ca-18ec-7b04-8a09-a7998bd60827.transcript",
    "agreement_status": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.final_agreement.status",
    "agreement_summary": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.final_agreement.summary",
    "origin": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.load.origin",
    "destination": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.load.destination",
    "equipment": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.load.equipment",
    "weight": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.load.weight",
    "mc_number": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.carrier.mc_number",
    "carrier_status": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.carrier.status",
    "currency": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.financials.currency",
    "final_rate": "019d87d2-f9b2-745c-b862-fd9fc22fe4bc.response.entities.financials.final_rate_accepted",
}


def get_mapped_fields(nested: dict) -> dict:
    return {alias: nested.get(raw_key) for alias, raw_key in FIELD_MAP.items()}


def to_numeric_series(values) -> list[float]:
    if not values:
        return []
    s = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    return s.tolist()


def extract_negotiation_metrics(negotiation_flow: list[dict]) -> dict:
    numeric_values = to_numeric_series(
        [step.get("value") for step in negotiation_flow if step.get("value") is not None]
    )

    carrier_offers = to_numeric_series(
        [
            step.get("value")
            for step in negotiation_flow
            if step.get("actor") == "user" and step.get("value") is not None
        ]
    )

    broker_offers = to_numeric_series(
        [
            step.get("value")
            for step in negotiation_flow
            if step.get("actor") == "assistant" and step.get("value") is not None
        ]
    )

    initial_offer = numeric_values[0] if numeric_values else np.nan

    return {
        "initial_offer": initial_offer,
        "carrier_max_offer": max(carrier_offers) if carrier_offers else np.nan,
        "broker_max_offer": max(broker_offers) if broker_offers else np.nan,
        "negotiation_rounds": len(carrier_offers),
    }


def build_route(origin, destination) -> str:
    return f"{origin or 'Unknown'} → {destination or 'Unknown'}"


def calculate_margin_pct(final_rate, initial_offer):
    if pd.isna(final_rate) or pd.isna(initial_offer) or initial_offer == 0:
        return np.nan
    return ((final_rate - initial_offer) / initial_offer) * 100


def calculate_duration_minutes(timestamp, completed_at):
    if pd.isna(timestamp) or pd.isna(completed_at):
        return np.nan
    return (completed_at - timestamp).total_seconds() / 60


def parse_single_run(run: dict) -> dict:
    nested = run.get("data", {})
    fields = get_mapped_fields(nested)

    negotiation_flow = safe_json_loads(fields["negotiation_flow"], [])
    tool_usage = safe_json_loads(fields["tool_usage"], [])
    key_insights = safe_json_loads(fields["key_insights"], [])
    transcript = safe_json_loads(fields["transcript"], [])

    timestamp = pd.to_datetime(run.get("timestamp"), errors="coerce")
    completed_at = pd.to_datetime(run.get("completed_at"), errors="coerce")
    final_rate = pd.to_numeric(fields["final_rate"], errors="coerce")

    negotiation = extract_negotiation_metrics(negotiation_flow)
    route = build_route(fields["origin"], fields["destination"])

    return {
        "run_id": run.get("id"),
        "status": run.get("status"),
        "timestamp": timestamp,
        "completed_at": completed_at,
        "input_tokens": pd.to_numeric(run.get("input_tokens"), errors="coerce"),
        "output_tokens": pd.to_numeric(run.get("output_tokens"), errors="coerce"),
        "classification": fields["classification"],
        "reasoning": fields["reasoning"],
        "agreement_status": fields["agreement_status"],
        "agreement_summary": fields["agreement_summary"],
        "origin": fields["origin"],
        "destination": fields["destination"],
        "equipment": fields["equipment"],
        "weight": fields["weight"],
        "mc_number": fields["mc_number"],
        "carrier_status": fields["carrier_status"],
        "currency": fields["currency"],
        "final_rate": final_rate,
        "initial_offer": negotiation["initial_offer"],
        "negotiation_rounds": negotiation["negotiation_rounds"],
        "tool_count": len(tool_usage),
        "transcript_turns": len(transcript),
        "key_insights": " | ".join(key_insights) if key_insights else None,
        "route": route,
        "carrier_max_offer": negotiation["carrier_max_offer"],
        "broker_max_offer": negotiation["broker_max_offer"],
        "margin_vs_initial_pct": calculate_margin_pct(final_rate, negotiation["initial_offer"]),
        "duration_minutes": calculate_duration_minutes(timestamp, completed_at),
        "negotiation_flow_raw": negotiation_flow,
        "tool_usage_raw": tool_usage,
        "transcript_raw": transcript,
    }


def parse_runs_to_dataframe(api_response: dict) -> pd.DataFrame:
    runs = api_response.get("data", [])
    rows = [parse_single_run(run) for run in runs]

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["date"] = df["timestamp"].dt.date
    df["day"] = df["timestamp"].dt.day_name()

    return df

def build_negotiation_steps_df(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, run in df.iterrows():
        for i, step in enumerate(run["negotiation_flow_raw"]):
            rows.append({
                "run_id": run["run_id"],
                "route": run["route"],
                "step_index": i + 1,
                "actor": step.get("actor"),
                "step": step.get("step"),
                "value": pd.to_numeric(step.get("value"), errors="coerce"),
                "timestamp": run["timestamp"],
            })
    return pd.DataFrame(rows)

def build_tool_usage_df(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, run in df.iterrows():
        for tool in run["tool_usage_raw"]:
            rows.append({
                "run_id": run["run_id"],
                "tool_name": tool.get("tool_name"),
                "purpose": tool.get("purpose"),
                "result_summary": tool.get("result_summary"),
                "timestamp": run["timestamp"],
            })
    return pd.DataFrame(rows)

# ---------------------------
# UI
# ---------------------------
st.title("🤖 AI Call Analysis")

Number_of_Calls = st.selectbox("Call amount", [25, 50, 100, "Custom"], index=2)

if Number_of_Calls == "Custom":
    page_size = st.number_input("Enter custom Call Amount", min_value=1, value=100)
else:
    page_size = Number_of_Calls

if st.button("Fetch AI Calls", use_container_width=True):
    try:
        with st.spinner("Fetching workflow runs..."):
            api_response = fetch_happyrobot_runs(HAPPYROBOT_WORKFLOW_ID,HAPPYROBOT_TOKEN,page=1, page_size=page_size)
            parsed_df = parse_runs_to_dataframe(api_response)
            steps_df = build_negotiation_steps_df(parsed_df)
            tools_df = build_tool_usage_df(parsed_df)

            st.session_state.ai_runs_raw = api_response
            st.session_state.ai_runs_df = parsed_df
            st.session_state.ai_steps_df = steps_df
            st.session_state.ai_tools_df = tools_df

        st.success("AI call data loaded successfully.")

    except KeyError as e:
        st.error(f"Missing secret: {e}. Check .streamlit/secrets.toml")
    except requests.HTTPError as e:
        st.error(f"HTTP error: {e}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

if "ai_runs_df" not in st.session_state or st.session_state.ai_runs_df.empty:
    st.info("Press 'Fetch AI Calls' to load data.")
    st.stop()

df = st.session_state.ai_runs_df.copy()
steps_df = st.session_state.ai_steps_df.copy()
tools_df = st.session_state.ai_tools_df.copy()

# ---------------------------
# Filters
# ---------------------------
st.subheader("Filters")

f1, f2, f3, f4 = st.columns(4)

with f1:
    status_filter = st.multiselect("Status", sorted(df["status"].dropna().unique().tolist()))

with f2:
    classification_filter = st.multiselect("Classification", sorted(df["classification"].dropna().unique().tolist()))

with f3:
    route_filter = st.multiselect("Route", sorted(df["route"].dropna().unique().tolist()))

with f4:
    equipment_filter = st.multiselect("Equipment", sorted(df["equipment"].dropna().unique().tolist()))

filtered_df = df.copy()

if status_filter:
    filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

if classification_filter:
    filtered_df = filtered_df[filtered_df["classification"].isin(classification_filter)]

if route_filter:
    filtered_df = filtered_df[filtered_df["route"].isin(route_filter)]

if equipment_filter:
    filtered_df = filtered_df[filtered_df["equipment"].isin(equipment_filter)]

if filtered_df.empty:
    st.warning("No runs match the selected filters.")
    st.stop()

filtered_run_ids = set(filtered_df["run_id"].tolist())
steps_df = steps_df[steps_df["run_id"].isin(filtered_run_ids)]
tools_df = tools_df[tools_df["run_id"].isin(filtered_run_ids)]

# ---------------------------
# KPIs
# ---------------------------
total_runs = len(filtered_df)
completed_runs = (filtered_df["status"] == "completed").sum()
success_rate = (completed_runs / total_runs * 100) if total_runs else np.nan
avg_final_rate = filtered_df["final_rate"].mean()
avg_margin = filtered_df["margin_vs_initial_pct"].mean()
avg_input_tokens = filtered_df["input_tokens"].mean()
avg_rounds = filtered_df["negotiation_rounds"].mean()

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Total Runs", fmt_number(total_runs))
k2.metric("Completed", fmt_number(completed_runs))
k3.metric("Success Rate", "-" if pd.isna(success_rate) else f"{success_rate:.1f}%")
k4.metric("Avg Final Rate", fmt_currency(avg_final_rate, 0))
k5.metric("Avg Margin vs Initial", "-" if pd.isna(avg_margin) else f"{avg_margin:.1f}%")
k6.metric("Avg Negotiation Rounds", fmt_number(avg_rounds, 1))

st.divider()

# ---------------------------
# Charts
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Runs Over Time")
    if "timestamp" in filtered_df.columns and filtered_df["timestamp"].notna().any():
        runs_over_time = (
            filtered_df
            .dropna(subset=["timestamp"])
            .set_index("timestamp")
            .resample("D")
            .size()
            .reset_index(name="runs")
        )
        fig = px.line(
            runs_over_time,
            x="timestamp",
            y="runs",
            markers=True,
            template="plotly_white",
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title="Runs")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Final Rate Distribution")
    rate_df = filtered_df.dropna(subset=["final_rate"])
    if not rate_df.empty:
        fig = px.histogram(
            rate_df,
            x="final_rate",
            nbins=25,
            template="plotly_white",
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Final Rate ($)", yaxis_title="Runs")
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Top Routes")
    route_counts = (
        filtered_df["route"]
        .value_counts()
        .reset_index()
    )
    route_counts.columns = ["route", "count"]

    if not route_counts.empty:
        fig = px.bar(
            route_counts.head(10).sort_values("count", ascending=True),
            x="count",
            y="route",
            orientation="h",
            text="count",
            template="plotly_white",
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Runs", yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Tool Usage")
    if not tools_df.empty:
        tool_counts = tools_df["tool_name"].value_counts().reset_index()
        tool_counts.columns = ["tool_name", "count"]

        fig = px.pie(
            tool_counts,
            names="tool_name",
            values="count",
            hole=0.55,
            template="plotly_white",
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Negotiation flow
# ---------------------------
st.subheader("Negotiation Flow")

run_ids = filtered_df["run_id"].tolist()
run_options = ["All runs"] + run_ids

run_label_map = {
    row["run_id"]: f"Run {i+1} · {row['route']}"
    for i, (_, row) in enumerate(filtered_df.reset_index(drop=True).iterrows())
}

selected_run_id = st.selectbox(
    "Select Run",
    options=run_options,
    format_func=lambda x: "All runs" if x == "All runs" else run_label_map.get(x, str(x))
)

if selected_run_id == "All runs":
    selected_steps = steps_df.copy()
else:
    selected_steps = steps_df[steps_df["run_id"] == selected_run_id].copy()

if not selected_steps.empty:
    selected_steps = selected_steps.copy()
    selected_steps["run_label"] = selected_steps["run_id"].map(run_label_map)
    selected_steps["run_actor"] = (
        selected_steps["run_label"].fillna(selected_steps["run_id"].astype(str))
        + " | "
        + selected_steps["actor"].astype(str)
    )

    chart_df = selected_steps.dropna(subset=["value"]).copy()

    if not chart_df.empty:
        fig = px.line(
            chart_df,
            x="step_index",
            y="value",
            color="actor",
            line_group="run_actor",
            line_dash="run_label" if selected_run_id == "All runs" else None,
            markers=True,
            hover_data={
                "run_label": True,
                "actor": True,
                "step": True,
                "run_id": False,
            },
            template="plotly_white",
            color_discrete_map={
                "user": "#1f77b4",
                "assistant": "#d62728",
                "User": "#1f77b4",
                "Assistant": "#d62728",
            },
        )

        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Negotiation Step",
            yaxis_title="Rate ($)",
        )

        st.plotly_chart(fig, use_container_width=True)

    display_cols = (
        ["step_index", "actor", "step", "value"]
    )
    if selected_run_id != "All runs":
        st.dataframe(
            selected_steps[display_cols],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No negotiation steps available for this selection.")

st.divider()
# ---------------------------
# Details
# ---------------------------
st.subheader("Run Details")

detail_cols = [
    "timestamp", "status", "classification", "route", "equipment",
    "final_rate", "initial_offer", "margin_vs_initial_pct",
    "negotiation_rounds", "tool_count", "input_tokens", "output_tokens",
    "duration_minutes", "mc_number", "carrier_status", "agreement_status",
    "agreement_summary", "key_insights"
]

available_detail_cols = [c for c in detail_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[available_detail_cols].sort_values("timestamp", ascending=False),
    use_container_width=True,
    hide_index=True,
)