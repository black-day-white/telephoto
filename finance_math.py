import numpy as np
import pandas as pd

def calculate_risk_score(q1_answer, q2_answer, q3_answer):
    """
    Computes a risk profile based on questionnaire points (out of 9).
    """
    score = q1_answer + q2_answer + q3_answer
    if score <= 4:
        return "Conservative", {
            "Debt Funds & Fixed Income": 60,
            "Large Cap Index Funds": 25,
            "Gold / Sovereign Gold Bonds": 15
        }
    elif score <= 7:
        return "Moderate", {
            "Large & Mid Cap Equities": 50,
            "Corporate Bonds / Debt": 35,
            "Gold / Commodities": 15
        }
    else:
        return "Aggressive", {
            "Flexi & Mid/Small Cap Equities": 70,
            "Liquid / Debt Funds": 15,
            "Gold / Alternative Assets": 15
        }

def calculate_sip_projection(monthly_investment, years, annual_rate):
    """
    Calculates monthly compounding for a regular SIP.
    Formula: M * [((1 + r)^n - 1) / r] * (1 + r)
    """
    months = np.arange(1, (years * 12) + 1)
    monthly_rate = annual_rate / 12 / 100
    
    invested_capital = months * monthly_investment
    portfolio_value = monthly_investment * (((1 + monthly_rate)**months - 1) / monthly_rate) * (1 + monthly_rate)
    
    df = pd.DataFrame({
        "Year": months / 12,
        "Total Invested (₹)": np.round(invested_capital),
        "Estimated Value (₹)": np.round(portfolio_value)
    })
    return df
