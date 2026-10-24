
import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
from pathlib import Path

# file locations
project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / "data"
executable = project_dir / "cpp" / "ercot"

# website setup
st.set_page_config(page_title="ERCOT Electricity Explorer", layout="wide")

st.title("ERCOT Electricity Price Explorer")
st.write("Electricity price analysis using C++ and Python")
st.caption("Source: ERCOT Real-Time Market | HB_HOUSTON | 2026")

# read the original prices
prices = pd.read_csv(data_dir / "prices.csv")
prices["Date"] = pd.to_datetime(prices["Date"])

# filters
st.subheader("Analysis Filters")

threshold = st.slider(
    "Price spike threshold ($/MWh)",
    min_value=0,
    max_value=1500,
    value=100,
    step=25
)

min_date = prices["Date"].min().date()
max_date = prices["Date"].max().date()

selected_dates = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# make sure both dates are selected
if len(selected_dates) != 2:
    st.info("Please select a start and end date.")
    st.stop()

start_date, end_date = selected_dates

# only keep prices within the selected dates
filtered_prices = prices[
    (prices["Date"].dt.date >= start_date) &
    (prices["Date"].dt.date <= end_date)
]

if filtered_prices.empty:
    st.warning("No data found for these dates.")
    st.stop()

# run C++ with the selected filters
try:
    subprocess.run(
        [str(executable), str(threshold), str(start_date), str(end_date)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=True,
        timeout=15
    )
except (OSError, subprocess.CalledProcessError,
        subprocess.TimeoutExpired) as error:
    st.error(f"Error running C++: {error}")
    st.stop()

# load the files created by C++
hourly = pd.read_csv(data_dir / "hourly_averages.csv")
daily = pd.read_csv(data_dir / "daily_averages.csv")
summary = pd.read_csv(data_dir / "summary.csv")
spikes = pd.read_csv(data_dir / "spikes.csv")

daily["Date"] = pd.to_datetime(daily["Date"])

# overall price statistics
st.subheader("Electricity Price Statistics")

col1, col2, col3 = st.columns(3)

col1.metric("Average Price", f"${summary['Average'][0]:.2f}/MWh")
col2.metric("Minimum Price", f"${summary['Minimum'][0]:.2f}/MWh")
col3.metric("Maximum Price", f"${summary['Maximum'][0]:.2f}/MWh")

# hourly average graph
st.subheader("Hourly Electricity Price Trends")

hourly_fig = px.line(
    hourly,
    x="Hour",
    y="AveragePrice",
    markers=True,
    title="Average Price by Hour",
    labels={
        "Hour": "Hour of Day",
        "AveragePrice": "Average Price ($/MWh)"
    }
)

hourly_fig.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(hourly_fig, width="stretch")

with st.expander("View Hourly Price Data"):
    st.dataframe(hourly, width="stretch")

# daily average graph
st.subheader("Daily Electricity Price Trends")

daily_fig = px.line(
    daily,
    x="Date",
    y="AveragePrice",
    markers=True,
    title="Average Price by Day",
    labels={
        "AveragePrice": "Average Price ($/MWh)"
    }
)

st.plotly_chart(daily_fig, width="stretch")

with st.expander("View Daily Price Data"):
    st.dataframe(daily, width="stretch")

# price distribution
st.subheader("Electricity Price Distribution")

hist = px.histogram(
    filtered_prices,
    x="Price",
    nbins=60,
    title="Distribution of Electricity Prices"
)

hist.update_layout(
    xaxis_title="Price ($/MWh)",
    yaxis_title="Number of Observations"
)

hist.add_vline(x=threshold, line_dash="dash", line_color="red")

st.plotly_chart(hist, width="stretch")

# load the detailed data for the timeline
detailed = pd.read_csv(data_dir / "prices_detailed.csv")
detailed["Date"] = pd.to_datetime(detailed["Date"])

# only keep dates in the selected range
timeline = detailed[
    (detailed["Date"].dt.date >= start_date) &
    (detailed["Date"].dt.date <= end_date)
].copy()

# calculate the actual time of each 15-minute interval
timeline["Hour"] = timeline["DeliveryHour"] - 1
timeline["Minute"] = (timeline["DeliveryInterval"] - 1) * 15

timeline["Timestamp"] = (
    timeline["Date"] +
    pd.to_timedelta(timeline["Hour"], unit="h") +
    pd.to_timedelta(timeline["Minute"], unit="m")
)

# mark prices that are above the threshold
timeline["Spike"] = timeline["Price"] > threshold

# price spike timeline
st.subheader("Electricity Price Spike Timeline")

timeline_fig = px.scatter(
    timeline,
    x="Timestamp",
    y="Price",
    color="Spike",
    color_discrete_map={False: "steelblue", True: "red"},
    title="15-Minute Electricity Prices",
    labels={
        "Timestamp": "Date and Time",
        "Price": "Price ($/MWh)",
        "Spike": "Price Spike"
    }
)

timeline_fig.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red"
)

st.plotly_chart(timeline_fig, width="stretch")

# top 10 highest prices
st.subheader("Top 10 Highest Electricity Prices")

top10 = timeline.nlargest(10, "Price").copy()
top10 = top10.reset_index(drop=True)

# create rankings
top10.insert(0, "Rank", range(1, len(top10) + 1))

# format the date and time
top10["Date"] = top10["Timestamp"].dt.strftime("%Y-%m-%d")
top10["Time"] = top10["Timestamp"].dt.strftime("%I:%M %p")

top10 = top10[["Rank", "Date", "Time", "Price"]]

st.dataframe(
    top10,
    column_config={
        "Price": st.column_config.NumberColumn(
            "Price ($/MWh)",
            format="$%.2f"
        )
    },
    hide_index=True,
    width="stretch"
)

# price spike statistics
st.subheader("Detected Electricity Price Spikes")

spike_count = len(spikes)
total_count = len(filtered_prices)
spike_percent = spike_count / total_count * 100

col1, col2, col3 = st.columns(3)

col1.metric("Selected Threshold", f"${threshold}/MWh")
col2.metric("Detected Spikes", spike_count)
col3.metric("Spike Frequency", f"{spike_percent:.1f}%")

if not spikes.empty:
    st.dataframe(spikes, width="stretch")
else:
    st.info("No prices exceeded the selected threshold.")

# footer
st.divider()
st.caption("Built with C++, Python, Pandas, Plotly, and Streamlit.")
