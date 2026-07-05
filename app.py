import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. SETUP PAGE
st.set_page_config(page_title="Orbit Ecosystem | Impact Dashboard", page_icon="🚀", layout="wide")

# 2. SIDEBAR: TOGGLES & DYNAMIC LOGOS
# Move toggles to the top so the logo can react to the choice
company = st.sidebar.radio("🏢 Select Organization", ["Orbit Innovation Hub", "Orbit Health"])

# Dynamic Logo Logic
if company == "Orbit Innovation Hub" and os.path.exists("oih_logo.png"):
    st.sidebar.image("oih_logo.png", use_container_width=True)
elif company == "Orbit Health" and os.path.exists("oh_logo.png"):
    st.sidebar.image("oh_logo.png", use_container_width=True)
else:
    st.sidebar.title(company)

st.sidebar.divider()

# Multi-Platform Toggle (Placeholder for future data)
platform = st.sidebar.selectbox("📱 Select Platform", ["LinkedIn", "Facebook", "X (Twitter)", "Telegram", "TikTok", "Instagram"])

st.sidebar.divider()

# 3. SMART DATA LOADER (Handles both Local and GitHub file structures)
@st.cache_data
def load_csv(filename, skip_rows=0, date_col=None):
    # Check if file is in the root folder (GitHub structure)
    if os.path.exists(filename):
        filepath = filename
    # Check if file is in a 'data' folder (Local structure)
    elif os.path.exists(os.path.join("data", filename)):
        filepath = os.path.join("data", filename)
    else:
        return pd.DataFrame() # Return empty if not found
        
    try:
        df = pd.read_csv(filepath, skiprows=skip_rows)
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(date_col)
        return df
    except:
        return pd.DataFrame()

# Load datasets
df_metrics = load_csv("Content - Metrics.csv", skip_rows=1, date_col="Date")
df_posts = load_csv("Content - All posts.csv", skip_rows=1, date_col="Created date")
df_competitors = load_csv("Competitor Analytics - COMPETITORS.csv", skip_rows=1)
df_visitors = load_csv("Visitors - Visitor metrics.csv", date_col="Date")
df_followers_growth = load_csv("Followers - New followers.csv", date_col="Date")

# 4. EXACT DATE INPUT FILTER
st.sidebar.subheader("📅 Filter by Specific Dates")
if not df_metrics.empty:
    min_date = df_metrics['Date'].min().date()
    max_date = df_metrics['Date'].max().date()
    
    # User inputs specific dates
    try:
        date_selection = st.sidebar.date_input(
            "Select Start and End Date",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        # Unpack selection
        if len(date_selection) == 2:
            start_date, end_date = date_selection
        else:
            start_date = end_date = date_selection[0]
            
    except:
        start_date, end_date = min_date, max_date

    # Filter all time-series dataframes based on exact dates
    df_metrics = df_metrics[(df_metrics['Date'].dt.date >= start_date) & (df_metrics['Date'].dt.date <= end_date)]
    if not df_posts.empty:
        df_posts = df_posts[(df_posts['Created date'].dt.date >= start_date) & (df_posts['Created date'].dt.date <= end_date)]
    if not df_visitors.empty:
        df_visitors = df_visitors[(df_visitors['Date'].dt.date >= start_date) & (df_visitors['Date'].dt.date <= end_date)]

# 5. HEADER & TOP KPIs
st.title(f"🚀 {company} Impact Dashboard")
st.write(f"Currently viewing analytics for **{platform}**")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label=f"Total {platform} Followers", value="9,884", delta="Verified")

if not df_metrics.empty:
    total_imp = df_metrics['Impressions (total)'].sum()
    total_clicks = df_metrics['Clicks (total)'].sum()
    avg_er = df_metrics['Engagement rate (total)'].mean() * 100
    
    col2.metric(label="Total Impressions", value=f"{total_imp:,.0f}")
    col3.metric(label="Total Clicks", value=f"{total_clicks:,.0f}")
    col4.metric(label="Avg. Engagement Rate", value=f"{avg_er:.2f}%")

st.divider()

# 6. PROGRESSIVE DISCLOSURE: TABS
tab1, tab2, tab3, tab4 = st.tabs(["📊 Content Performance", "👥 Audience Demographics", "📈 Traffic & Growth", "🏆 Competitors"])

# --- TAB 1: CONTENT PERFORMANCE ---
with tab1:
    st.subheader(f"{platform} Engagement Trends")
    if not df_metrics.empty:
        metric_choice = st.selectbox(
            "Select Metric to Visualize:", 
            ["Impressions (total)", "Clicks (total)", "Reactions (total)", "Comments (total)"]
        )
        
        fig_metrics = px.line(df_metrics, x="Date", y=metric_choice, markers=True)
        fig_metrics.update_traces(line_color='#005B5C')
        st.plotly_chart(fig_metrics, use_container_width=True)
        
    if not df_posts.empty:
        with st.expander("📂 View Top Performing Posts (Raw Data)"):
            display_cols = ['Created date', 'Post title', 'Impressions', 'Clicks', 'Engagement rate']
            st.dataframe(df_posts[display_cols].sort_values(by="Impressions", ascending=False), use_container_width=True)
    else:
        st.info("No content data available for this date range/platform.")

# --- TAB 2: AUDIENCE DEMOGRAPHICS ---
with tab2:
    st.subheader(f"Who is in our {platform} ecosystem?")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        user_type = st.radio("Select Audience Type:", ["Followers", "Visitors"])
    with col_b:
        demo_category = st.radio("Select Demographic Category:", ["Seniority", "Job function", "Company size", "Industry", "Location"], horizontal=True)
    
    demo_file = f"{user_type} - {demo_category}.csv"
    df_demo = load_csv(demo_file)
    
    if not df_demo.empty:
        y_col = "Total followers" if user_type == "Followers" else "Total views"
        df_demo = df_demo.sort_values(by=y_col, ascending=False).head(15)
        
        if demo_category == "Company size":
            fig_demo = px.pie(df_demo, names=demo_category, values=y_col, color_discrete_sequence=px.colors.sequential.Teal)
        else:
            fig_demo = px.bar(df_demo, x=demo_category, y=y_col, color_discrete_sequence=['#005B5C'])
            
        st.plotly_chart(fig_demo, use_container_width=True)
        with st.expander(f"📂 View raw {user_type} {demo_category} data"):
            st.dataframe(df_demo, use_container_width=True)
    else:
        st.warning(f"Data for '{demo_file}' is not available yet. Please upload it to view this metric.")

# --- TAB 3: TRAFFIC & GROWTH ---
with tab3:
    if not df_visitors.empty:
        st.subheader("Page Traffic (Desktop vs Mobile)")
        fig_traffic = px.area(df_visitors, x="Date", y=["Total page views (mobile)", "Total page views (desktop)"], 
                              color_discrete_sequence=['#005B5C', '#A3D9D3'])
        st.plotly_chart(fig_traffic, use_container_width=True)
    else:
        st.info("Traffic data not available.")

# --- TAB 4: COMPETITORS ---
with tab4:
    if not df_competitors.empty:
        st.subheader("How do we stack up?")
        fig_comp = px.bar(df_competitors, x="Page", y="New Followers", color="Page", 
                          title="New Followers vs Competitors", color_discrete_sequence=['#005B5C', '#6c757d'])
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Competitor data not available.")
