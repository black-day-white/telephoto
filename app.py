import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from google import genai
import finance_math as finance_math

# --- Page Setup ---
st.set_page_config(page_title="FinAdvisor AI", layout="wide", page_icon="📈")
st.title("🛡️ AI-Powered Wealth & Goal Advisor")
st.caption("Personalized Asset Allocation, SIP Projection & Market-Aware AI Advisory")

# --- API Initialization ---
# Replace with your actual Gemini API Key
GEMINI_KEY = ""
client = genai.Client(api_key=GEMINI_KEY)

# --- Sidebar: User Inputs & Risk Profiler ---
st.sidebar.header("📋 Investor Profile")
monthly_sip = st.sidebar.number_input("Monthly SIP Capacity (₹)", min_value=1000, value=15000, step=500)
horizon_years = st.sidebar.slider("Investment Horizon (Years)", min_value=1, max_value=25, value=10)

st.sidebar.subheader("Risk Profiler Quiz")
q1 = st.sidebar.selectbox(
    "1. If markets drop 15% in a month:",
    options=[(1, "Sell to protect remaining money"), (2, "Do nothing and hold"), (3, "Invest more aggressively")],
    format_func=lambda x: x[1]
)[0]

q2 = st.sidebar.selectbox(
    "2. Primary financial goal:",
    options=[(1, "Capital preservation"), (2, "Balanced wealth growth"), (3, "Maximum wealth creation")],
    format_func=lambda x: x[1]
)[0]

q3 = st.sidebar.selectbox(
    "3. Emergency reserve status:",
    options=[(1, "Less than 1 month"), (2, "3 to 6 months covered"), (3, "More than 6 months covered")],
    format_func=lambda x: x[1]
)[0]

risk_profile, asset_allocation = finance_math.calculate_risk_score(q1, q2, q3)

# Store market analysis across tabs
if "market_summary" not in st.session_state:
    st.session_state.market_summary = "No market data analyzed yet; using long-term average trends."

# --- Main Layout: Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Portfolio & Projections", "📁 Market Data Analysis", "🤖 AI Advisor Insights"])

# ================= TAB 1: PORTFOLIO & PROJECTIONS =================
with tab1:
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader(f"Assigned Profile: **{risk_profile}**")
        fig_pie = px.pie(
            names=list(asset_allocation.keys()),
            values=list(asset_allocation.values()),
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("SIP Wealth Accumulation")
        rate = 9.0 if risk_profile == "Conservative" else (12.0 if risk_profile == "Moderate" else 14.5)
        df_projection = finance_math.calculate_sip_projection(monthly_sip, horizon_years, rate)
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_projection["Year"], y=df_projection["Total Invested (₹)"], name="Total Invested", line=dict(dash='dash', color='gray')))
        fig_line.add_trace(go.Scatter(x=df_projection["Year"], y=df_projection["Estimated Value (₹)"], name=f"Expected Value (~{rate}%)", line=dict(color='#00CC96')))
        fig_line.update_layout(xaxis_title="Years", yaxis_title="Amount in ₹", hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)

# ================= TAB 2: MARKET DATA ANALYSIS =================
with tab2:
    st.subheader("Real Market Data Integration")
    st.write("Fetch live Indian market indicators or upload the hackathon CSV.")
    
    data_source = st.radio("Choose Data Ingestion Method:", ["Fetch Live Market Data", "Upload Hackathon CSV"], horizontal=True)
    
    market_df = None
    
    if data_source == "Fetch Live Market Data":
        if st.button("Fetch Last 5 Days Indian Market Data"):
            with st.spinner("Downloading real-time prices for NIFTY 50, Bank Nifty, and Gold ETF..."):
                tickers = {
                    "NIFTY 50": "^NSEI",
                    "BANK NIFTY": "^NSEBANK",
                    "RELIANCE": "RELIANCE.NS",
                    "HDFC BANK": "HDFCBANK.NS",
                    "GOLDBEES": "GOLDBEES.NS"
                }
                raw_data = yf.download(list(tickers.values()), period="5d", interval="1d")['Close']
                # Rename columns back to clean names
                inverse_map = {v: k for k, v in tickers.items()}
                raw_data = raw_data.rename(columns=inverse_map)
                market_df = raw_data.dropna()
                st.session_state.market_df = market_df
                
    else:
        uploaded_file = st.file_uploader("Upload Market CSV provided by the hackathon", type=["csv"])
        if uploaded_file is not None:
            market_df = pd.read_csv(uploaded_file, index_col=0)
            st.session_state.market_df = market_df

    # Process and summarize if data is available
    if "market_df" in st.session_state and st.session_state.market_df is not None:
        df = st.session_state.market_df
        st.write("### Recent Market Closing Prices", df.tail(5))
        
        # Calculate percentage returns over the period
        returns = ((df.iloc[-1] - df.iloc[0]) / df.iloc[0]) * 100
        returns_df = pd.DataFrame({"Asset": returns.index, "Return (%)": returns.values.round(2)})
        
        st.write("### Short-Term Performance")
        st.dataframe(returns_df.T)

        # Plot trend
        fig_trend = px.line(df, title="Recent Asset Price Trajectory")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Build synthesis prompt for the AI
        summary_lines = [f"{row['Asset']}: {row['Return (%)']}%" for _, row in returns_df.iterrows()]
        st.session_state.market_summary = (
            "Recent Market Trend over last few trading sessions:\n" +
            "\n".join(summary_lines)
        )
        st.success("✅ Market trend synthesized! Switch to Tab 3 for contextual advisory.")

# ================= TAB 3: AI ADVISOR INSIGHTS =================
with tab3:
    st.subheader("Context-Aware AI Advisory Engine")
    st.info(f"**Current Market Context Ingested:**\n\n{st.session_state.market_summary}")
    
    if st.button("Generate Strategy & Action Plan"):
        system_prompt = f"""
        You are a SEBI-compliant fiduciary financial planning advisor.
        
        Investor Parameters:
        - Monthly SIP Capacity: ₹{monthly_sip}
        - Investment Horizon: {horizon_years} years
        - Risk Classification: {risk_profile}
        - Recommended Asset Weights: {asset_allocation}
        
        Recent Market Performance Context:
        {st.session_state.market_summary}

        Instructions:
        1. Contextual Rationale: Explain how this asset allocation protects and grows their wealth specifically considering the recent market movements mentioned above.
        2. Execution Plan: Provide 3 concrete, beginner-friendly steps (e.g., how to deploy the ₹{monthly_sip}/month across broad index funds, gold, and liquid funds).
        3. Tactical Advice: What should the investor do if market volatility continues in the next 1–2 weeks? (e.g., Dollar-cost averaging / SIP discipline).
        4. Guardrails: Do not promise fixed percentage returns or recommend high-risk penny stocks. End with a standard statutory disclaimer.
        """
        
        with st.spinner("AI is analyzing asset models and generating your market-informed advisory plan..."):
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=system_prompt
            )
            st.markdown(response.text)
