import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Cash Runway Calculator", page_icon="💰", layout="wide")

# Styling
st.markdown("""
<style>
    .metric-card {
        background: #1b3a26; border-radius: 12px; padding: 20px;
        border-left: 4px solid #4ade80; color: #ffffff;
    }
    .metric-card h3 { color: #4ade80; margin: 0 0 8px 0; }
    .metric-card h2 { color: #ffffff; margin: 0 0 8px 0; }
    .metric-card p { color: #a1a1aa; margin: 0; }
    .warning-card {
        background: #3a3520; border-radius: 12px; padding: 20px;
        border-left: 4px solid #fbbf24; color: #ffffff;
    }
    .warning-card h3 { color: #fbbf24; margin: 0 0 8px 0; }
    .warning-card h2 { color: #ffffff; margin: 0 0 8px 0; }
    .warning-card p { color: #a1a1aa; margin: 0; }
    .danger-card {
        background: #3a1b1b; border-radius: 12px; padding: 20px;
        border-left: 4px solid #f87171; color: #ffffff;
    }
    .danger-card h3 { color: #f87171; margin: 0 0 8px 0; }
    .danger-card h2 { color: #ffffff; margin: 0 0 8px 0; }
    .danger-card p { color: #a1a1aa; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.title("💰 Startup Cash Runway Calculator")
st.markdown("Model your burn rate, forecast runway under multiple scenarios, and plan your next fundraise.")
st.divider()

# --- Sidebar Inputs ---
st.sidebar.header("Company Financials")
cash_balance = st.sidebar.number_input("Current Cash Balance ($)", min_value=0, value=2_000_000, step=50_000, format="%d")

st.sidebar.subheader("Monthly Revenue")
monthly_revenue = st.sidebar.number_input("Current Monthly Revenue ($)", min_value=0, value=150_000, step=10_000, format="%d")
revenue_growth_rate = st.sidebar.slider("Monthly Revenue Growth (%)", -10.0, 30.0, 5.0, 0.5)

st.sidebar.subheader("Monthly Expenses")
payroll = st.sidebar.number_input("Payroll ($)", min_value=0, value=180_000, step=5_000, format="%d")
rent_infra = st.sidebar.number_input("Rent and Infrastructure ($)", min_value=0, value=25_000, step=1_000, format="%d")
software_tools = st.sidebar.number_input("Software and Tools ($)", min_value=0, value=15_000, step=1_000, format="%d")
marketing = st.sidebar.number_input("Marketing and Sales ($)", min_value=0, value=40_000, step=5_000, format="%d")
other_expenses = st.sidebar.number_input("Other Expenses ($)", min_value=0, value=10_000, step=1_000, format="%d")
expense_growth_rate = st.sidebar.slider("Monthly Expense Growth (%)", -5.0, 20.0, 2.0, 0.5)

st.sidebar.subheader("Auto-Calculated Inputs")
cogs_pct = st.sidebar.slider("COGS as % of Revenue", 5.0, 60.0, 20.0, 1.0)
cogs = round(monthly_revenue * cogs_pct / 100)
st.sidebar.caption(f"COGS: ${cogs:,.0f}/mo (auto-calculated)")

total_monthly_expenses = payroll + rent_infra + software_tools + marketing + cogs + other_expenses

accounts_receivable = round(monthly_revenue * 0.8)
accounts_payable = round(total_monthly_expenses * 0.3)
other_assets = 50_000
other_liabilities = 30_000
st.sidebar.caption(f"Accounts Receivable: ${accounts_receivable:,.0f} (based on revenue)")
st.sidebar.caption(f"Accounts Payable: ${accounts_payable:,.0f} (based on expenses)")

st.sidebar.subheader("SaaS Metrics")
customer_count = st.sidebar.number_input("Current Customer Count", min_value=1, value=200, step=10, format="%d")
monthly_churn_rate = st.sidebar.slider("Monthly Churn Rate (%)", 0.0, 15.0, 3.0, 0.5)
customer_growth_rate = st.sidebar.slider("Monthly New Customer Growth (%)", 0.0, 30.0, 8.0, 0.5)

st.sidebar.subheader("Scenario Adjustments")
worst_revenue_multiplier = st.sidebar.slider("Worst Case: Revenue Multiplier", 0.3, 1.0, 0.6, 0.05)
worst_expense_multiplier = st.sidebar.slider("Worst Case: Expense Multiplier", 1.0, 2.0, 1.3, 0.05)
best_revenue_multiplier = st.sidebar.slider("Best Case: Revenue Multiplier", 1.0, 3.0, 1.5, 0.1)
best_expense_multiplier = st.sidebar.slider("Best Case: Expense Multiplier", 0.5, 1.0, 0.85, 0.05)

analyze = st.sidebar.button("🚀 Analyze Runway", use_container_width=True, type="primary")

if not analyze:
    st.info("Configure your inputs in the sidebar and click **Analyze Runway** to see results.")
    st.stop()

with st.spinner("Crunching the numbers..."):
    time.sleep(1.5)
st.balloons()

# Core Calculations
forecast_months = 36

def calculate_runway(cash, revenue, rev_growth, expenses, exp_growth, months):
    data = []
    running_cash, monthly_rev, monthly_exp = cash, revenue, expenses
    for month in range(1, months + 1):
        net_burn = monthly_exp - monthly_rev
        running_cash -= net_burn
        data.append({"Month": month, "Revenue": round(monthly_rev), "Expenses": round(monthly_exp), "Net Burn": round(net_burn), "Cash Balance": round(running_cash)})
        if running_cash <= 0:
            break
        monthly_rev *= (1 + rev_growth / 100)
        monthly_exp *= (1 + exp_growth / 100)
    return pd.DataFrame(data)

def calculate_full_projection(cash, revenue, rev_growth, expenses, exp_growth, months, customers, churn, cust_growth, cogs_val, ar, ap, o_assets, o_liab):
    data = []
    running_cash, monthly_rev, monthly_exp, monthly_cogs = cash, revenue, expenses, cogs_val
    current_customers, monthly_ar, monthly_ap = customers, ar, ap
    for month in range(1, months + 1):
        mrr, arr = monthly_rev, monthly_rev * 12
        churned_customers = round(current_customers * (churn / 100))
        new_customers = round(current_customers * (cust_growth / 100))
        current_customers = max(current_customers - churned_customers + new_customers, 1)
        arpu = mrr / current_customers if current_customers > 0 else 0
        cac = marketing / new_customers if new_customers > 0 else 0
        avg_lifetime = 1 / (churn / 100) if churn > 0 else 100
        ltv = arpu * avg_lifetime
        ltv_cac = ltv / cac if cac > 0 else 0
        nrr = ((mrr - (churned_customers * arpu)) / (mrr / (1 + rev_growth / 100))) * 100 if mrr > 0 else 0
        gross_profit = monthly_rev - monthly_cogs
        gross_margin = (gross_profit / monthly_rev * 100) if monthly_rev > 0 else 0
        total_opex = monthly_exp - monthly_cogs
        ebitda = gross_profit - total_opex
        gross_burn = monthly_exp
        net_burn = monthly_exp - monthly_rev
        running_cash -= net_burn
        months_remaining = running_cash / net_burn if net_burn > 0 else 999
        total_assets = running_cash + monthly_ar + o_assets
        total_liabilities = monthly_ap + o_liab
        equity = total_assets - total_liabilities
        data.append({
            "Month": month, "MRR": round(mrr), "ARR": round(arr), "Customers": round(current_customers),
            "New Customers": new_customers, "Churned": churned_customers, "ARPU": round(arpu),
            "CAC": round(cac), "LTV": round(ltv), "LTV/CAC": round(ltv_cac, 1),
            "NRR (%)": round(nrr, 1), "Churn Rate (%)": round(churn, 1),
            "Revenue": round(monthly_rev), "COGS": round(monthly_cogs), "Gross Profit": round(gross_profit),
            "Gross Margin (%)": round(gross_margin, 1), "OPEX": round(total_opex), "EBITDA": round(ebitda),
            "Net Income": round(ebitda), "Gross Burn": round(gross_burn), "Net Burn": round(net_burn),
            "Cash Balance": round(running_cash), "Runway (Months)": round(months_remaining, 1) if months_remaining < 999 else "N/A",
            "Cash": round(running_cash), "Accounts Receivable": round(monthly_ar), "Other Assets": round(o_assets),
            "Total Assets": round(total_assets), "Accounts Payable": round(monthly_ap),
            "Other Liabilities": round(o_liab), "Total Liabilities": round(total_liabilities), "Equity": round(equity),
        })
        if running_cash <= 0:
            break
        monthly_rev *= (1 + rev_growth / 100)
        monthly_exp *= (1 + exp_growth / 100)
        monthly_cogs = monthly_rev * cogs_pct / 100
        monthly_ar = monthly_rev * 0.8
        monthly_ap = monthly_exp * 0.3
    return pd.DataFrame(data)

base_df = calculate_runway(cash_balance, monthly_revenue, revenue_growth_rate, total_monthly_expenses, expense_growth_rate, forecast_months)
worst_df = calculate_runway(cash_balance, monthly_revenue * worst_revenue_multiplier, revenue_growth_rate * 0.5, total_monthly_expenses * worst_expense_multiplier, expense_growth_rate * 1.5, forecast_months)
best_df = calculate_runway(cash_balance, monthly_revenue * best_revenue_multiplier, revenue_growth_rate * 1.5, total_monthly_expenses * best_expense_multiplier, expense_growth_rate * 0.5, forecast_months)
full_df = calculate_full_projection(cash_balance, monthly_revenue, revenue_growth_rate, total_monthly_expenses, expense_growth_rate, forecast_months, customer_count, monthly_churn_rate, customer_growth_rate, cogs, accounts_receivable, accounts_payable, other_assets, other_liabilities)

def get_runway_months(df):
    negative = df[df["Cash Balance"] <= 0]
    return negative.iloc[0]["Month"] if len(negative) > 0 else forecast_months

base_runway = get_runway_months(base_df)
worst_runway = get_runway_months(worst_df)
best_runway = get_runway_months(best_df)
gross_burn = total_monthly_expenses
net_burn = total_monthly_expenses - monthly_revenue

# KEY METRICS
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Current Cash", f"${cash_balance:,.0f}")
with col2: st.metric("Gross Burn", f"${gross_burn:,.0f}/mo")
with col3: st.metric("Net Burn", f"${net_burn:,.0f}/mo")
with col4:
    if net_burn > 0: st.metric("Simple Runway", f"{cash_balance / net_burn:.1f} months")
    else: st.metric("Simple Runway", "Cash flow positive")
st.divider()

# SCENARIO ANALYSIS
h_col, i_col = st.columns([12, 1])
with h_col: st.header("Scenario Analysis")
with i_col:
    with st.popover("ℹ️"):
        st.markdown("""
**Current Status** classifies your company based on months of cash at current net burn:
- **18+ months**: Healthy. No immediate fundraise pressure.
- **12-18 months**: Stable but start planning a raise. Most take 3-6 months.
- **6-12 months**: Runway compressing. Fundraise or cut costs now.
- **Under 6 months**: Critical. Immediate action needed.

**Scenario cards** project runway under three assumptions. Worst case models revenue contraction + cost escalation. Baseline holds current trajectory. Best case models accelerated growth + cost efficiency. The runway number on each card shows months until cash hits zero.
""")

# Status box
if net_burn <= 0:
    status_text, status_color = "Cash Flow Positive", "#4ade80"
    status_desc = f"Cash position: ${cash_balance:,.0f}. Revenue exceeds OPEX. Net positive cash flow of ${abs(net_burn):,.0f}/mo."
elif cash_balance / net_burn >= 18:
    runway_num = cash_balance / net_burn
    status_text, status_color = "Strong Position", "#4ade80"
    status_desc = f"Cash position: ${cash_balance:,.0f}. Net burn: ${net_burn:,.0f}/mo. Implied runway: {runway_num:.1f} months. Above the 18-month threshold most VCs consider healthy."
elif cash_balance / net_burn >= 12:
    runway_num = cash_balance / net_burn
    status_text, status_color = "Monitor Closely", "#fbbf24"
    status_desc = f"Cash position: ${cash_balance:,.0f}. Net burn: ${net_burn:,.0f}/mo. Implied runway: {runway_num:.1f} months. Within the 12 to 18-month range where fundraise timing becomes a factor."
elif cash_balance / net_burn >= 6:
    runway_num = cash_balance / net_burn
    status_text, status_color = "Fundraise Now", "#fb923c"
    status_desc = f"Cash position: ${cash_balance:,.0f}. Net burn: ${net_burn:,.0f}/mo. Implied runway: {runway_num:.1f} months. Below the 12-month threshold. Runway is compressing."
else:
    runway_num = cash_balance / net_burn
    status_text, status_color = "Critical", "#f87171"
    status_desc = f"Cash position: ${cash_balance:,.0f}. Net burn: ${net_burn:,.0f}/mo. Implied runway: {runway_num:.1f} months. Below 6-month threshold. Operating at critical cash levels."

st.markdown(f"""<div style="background:#18181b;border-radius:12px;padding:24px;border:2px solid {status_color};margin-bottom:24px;">
    <p style="color:{status_color};font-size:14px;font-weight:600;margin:0 0 4px 0;">YOUR CURRENT STATUS</p>
    <h2 style="color:#ffffff;margin:0 0 8px 0;">{status_text}</h2>
    <p style="color:#a1a1aa;margin:0;font-size:15px;">{status_desc}</p>
</div>""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
worst_rev_start = monthly_revenue * worst_revenue_multiplier
worst_exp_start = total_monthly_expenses * worst_expense_multiplier
best_rev_start = monthly_revenue * best_revenue_multiplier
best_exp_start = total_monthly_expenses * best_expense_multiplier

with col1:
    label = f"{forecast_months}+ months" if worst_runway >= forecast_months else f"{worst_runway} months"
    color = "danger-card" if worst_runway < 12 else "warning-card"
    st.markdown(f"""<div class="{color}"><h3>Worst Case</h3><h2>{label}</h2><p style="font-size:13px;line-height:1.6;">What if revenue contracts and operating costs escalate? Revenue at ${worst_rev_start:,.0f}/mo ({worst_revenue_multiplier:.0%} of current), OPEX at ${worst_exp_start:,.0f}/mo ({worst_expense_multiplier:.0%} of current), decelerating MoM revenue growth, accelerating cost inflation. Think churn spike, failed product launch, or key customer loss.</p></div>""", unsafe_allow_html=True)
with col2:
    label = f"{forecast_months}+ months" if base_runway >= forecast_months else f"{base_runway} months"
    color = "danger-card" if base_runway < 12 else "metric-card"
    st.markdown(f"""<div class="{color}"><h3>Baseline</h3><h2>{label}</h2><p style="font-size:13px;line-height:1.6;">Current burn trajectory held constant. Revenue at ${monthly_revenue:,.0f}/mo with {revenue_growth_rate}% MoM growth, total OPEX at ${total_monthly_expenses:,.0f}/mo with {expense_growth_rate}% MoM increase. No fundraise, no major pivots, steady unit economics. Default path if nothing changes.</p></div>""", unsafe_allow_html=True)
with col3:
    label = f"{forecast_months}+ months" if best_runway >= forecast_months else f"{best_runway} months"
    st.markdown(f"""<div class="metric-card"><h3>Best Case</h3><h2>{label}</h2><p style="font-size:13px;line-height:1.6;">What if growth accelerates and you achieve operating leverage? Revenue at ${best_rev_start:,.0f}/mo ({best_revenue_multiplier:.0%} of current) with stronger MoM compounding, OPEX at ${best_exp_start:,.0f}/mo ({best_expense_multiplier:.0%} of current). Think successful upsell motion, lower CAC, or favorable contract renegotiations.</p></div>""", unsafe_allow_html=True)
st.divider()

# CASH BALANCE FORECASTS
h_col, i_col = st.columns([12, 1])
with h_col: st.header("Cash Balance Forecast")
with i_col:
    with st.popover("ℹ️"):
        st.markdown("""
**Burndown**: Baseline cash over 24 months with threshold markers at 18 months (safe), 12 months (fundraise trigger), and 6 months (critical). Watch how quickly the curve approaches each line.

**Fan Chart**: Confidence cone between worst and best case. Wider cone = more uncertainty. Check if worst case crosses zero within your forecast.

**Waterfall**: Month-by-month cash flow. Green bars = net positive months. Red bars = net burn months. Blue bars = starting and ending cash totals. Look for the transition from red to green (breakeven).
""")

chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Burndown", "Fan Chart", "Waterfall"])

with chart_tab1:
    fig_burn = go.Figure()
    fig_burn.add_trace(go.Scatter(x=base_df["Month"], y=base_df["Cash Balance"], name="Baseline", line=dict(color="#4ade80", width=3)))
    fig_burn.add_hline(y=0, line_dash="dot", line_color="#f87171", annotation_text="Cash Zero", annotation_position="bottom left")
    if net_burn > 0:
        fig_burn.add_hline(y=net_burn * 18, line_dash="dash", line_color="#4ade80", annotation_text="18-Month Safe Zone", annotation_position="top left", line_width=1)
        fig_burn.add_hline(y=net_burn * 12, line_dash="dash", line_color="#fbbf24", annotation_text="12-Month Fundraise Trigger", annotation_position="top left", line_width=1)
        fig_burn.add_hline(y=net_burn * 6, line_dash="dash", line_color="#fb923c", annotation_text="6-Month Critical", annotation_position="top left", line_width=1)
    fig_burn.update_layout(xaxis_title="Month", yaxis_title="Cash Balance ($)", yaxis_tickformat="$,.0f", template="plotly_dark", height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_burn, use_container_width=True)

with chart_tab2:
    fig_fan = go.Figure()
    max_len = min(len(worst_df), len(best_df))
    fig_fan.add_trace(go.Scatter(x=worst_df["Month"][:max_len], y=worst_df["Cash Balance"][:max_len], line=dict(color="rgba(248,113,113,0.3)"), showlegend=False))
    fig_fan.add_trace(go.Scatter(x=best_df["Month"][:max_len], y=best_df["Cash Balance"][:max_len], name="Confidence Range", fill="tonexty", fillcolor="rgba(74,222,128,0.08)", line=dict(color="rgba(74,222,128,0.3)")))
    fig_fan.add_trace(go.Scatter(x=worst_df["Month"], y=worst_df["Cash Balance"], name="Worst Case", line=dict(color="#f87171", dash="dash", width=1.5)))
    fig_fan.add_trace(go.Scatter(x=base_df["Month"], y=base_df["Cash Balance"], name="Baseline", line=dict(color="#4ade80", width=3)))
    fig_fan.add_trace(go.Scatter(x=best_df["Month"], y=best_df["Cash Balance"], name="Best Case", line=dict(color="#22d3ee", dash="dash", width=1.5)))
    fig_fan.add_hline(y=0, line_dash="dot", line_color="#f87171", annotation_text="Cash Zero")
    fig_fan.update_layout(xaxis_title="Month", yaxis_title="Cash Balance ($)", yaxis_tickformat="$,.0f", template="plotly_dark", height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_fan, use_container_width=True)

with chart_tab3:
    w_labels, w_values, w_measures = ["Starting Cash"], [cash_balance], ["absolute"]
    for _, row in base_df.iterrows():
        w_labels.append(f"M{int(row['Month'])}")
        w_values.append(-row["Net Burn"])
        w_measures.append("relative")
    w_labels.append("Ending Cash")
    w_values.append(base_df["Cash Balance"].iloc[-1])
    w_measures.append("total")
    fig_water = go.Figure(go.Waterfall(x=w_labels, y=w_values, measure=w_measures, increasing=dict(marker=dict(color="#4ade80")), decreasing=dict(marker=dict(color="#f87171")), totals=dict(marker=dict(color="#3b82f6")), connector=dict(line=dict(color="#555555", width=1))))
    fig_water.update_layout(xaxis_title="", yaxis_title="Cash ($)", yaxis_tickformat="$,.0f", template="plotly_dark", height=450, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_water, use_container_width=True)
st.divider()

# REVENUE VS EXPENSES
h_col, i_col = st.columns([12, 1])
with h_col: st.header("Revenue vs Expenses (Baseline)")
with i_col:
    with st.popover("ℹ️"):
        st.markdown("""
**Green line**: Monthly revenue. **Red line**: Monthly expenses.

**Red shaded area**: Months where expenses exceed revenue (burning cash).
**Green shaded area**: Months where revenue exceeds expenses (positive cash flow).

The crossover point where green overtakes red is your projected cash flow breakeven. If lines never cross within 24 months, the company does not reach profitability under current assumptions.
""")

fig_dual = go.Figure()
fig_dual.add_trace(go.Scatter(x=base_df["Month"], y=base_df["Revenue"], name="Revenue", line=dict(color="#4ade80", width=2.5)))
fig_dual.add_trace(go.Scatter(x=base_df["Month"], y=base_df["Expenses"], name="Expenses", line=dict(color="#f87171", width=2.5)))
for i in range(len(base_df) - 1):
    row, next_row = base_df.iloc[i], base_df.iloc[i + 1]
    mx = [row["Month"], next_row["Month"], next_row["Month"], row["Month"]]
    if row["Revenue"] >= row["Expenses"]:
        fig_dual.add_trace(go.Scatter(x=mx, y=[row["Revenue"], next_row["Revenue"], next_row["Expenses"], row["Expenses"]], fill="toself", fillcolor="rgba(74,222,128,0.15)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    else:
        fig_dual.add_trace(go.Scatter(x=mx, y=[row["Expenses"], next_row["Expenses"], next_row["Revenue"], row["Revenue"]], fill="toself", fillcolor="rgba(248,113,113,0.15)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig_dual.update_layout(xaxis_title="Month", yaxis_title="Amount ($)", yaxis_tickformat="$,.0f", template="plotly_dark", height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_dual, use_container_width=True)
st.divider()

# EXPENSE BREAKDOWN
h_col, i_col = st.columns([12, 1])
with h_col: st.header("Expense Breakdown")
with i_col:
    with st.popover("ℹ️"):
        st.markdown(f"""
Shows total monthly OPEX of ${total_monthly_expenses:,.0f} by category.

- **Payroll** (${payroll:,.0f}): {payroll/total_monthly_expenses*100:.0f}% of spend. Largest line item for most startups.
- **Marketing** (${marketing:,.0f}): {marketing/total_monthly_expenses*100:.0f}%. Tied to CAC.
- **COGS** (${cogs:,.0f}): {cogs/total_monthly_expenses*100:.0f}%. At {cogs_pct}% of revenue.

If payroll exceeds 60-70%, the company is heavily people-dependent. High COGS = lower gross margins.
""")

expense_data = {"Category": ["Payroll", "Rent & Infrastructure", "Software & Tools", "Marketing & Sales", "COGS", "Other"], "Amount": [payroll, rent_infra, software_tools, marketing, cogs, other_expenses]}
fig_pie = go.Figure(data=[go.Pie(labels=pd.DataFrame(expense_data)["Category"], values=pd.DataFrame(expense_data)["Amount"], hole=0.4, marker_colors=["#4ade80", "#3b82f6", "#fbbf24", "#f87171", "#a78bfa", "#6b7280"])])
fig_pie.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_pie, use_container_width=True)
st.divider()

# MONTHLY PROJECTIONS
h_col, i_col = st.columns([12, 1])
with h_col: st.header("Monthly Projections (Baseline)")
with i_col:
    with st.popover("ℹ️"):
        st.markdown("""
**SaaS Metrics**: MRR, ARR, customer count, ARPU, CAC, LTV, LTV/CAC ratio (healthy > 3.0), NRR (healthy > 100%), churn rate.
**P&L**: Revenue, COGS, gross profit, gross margin (healthy SaaS: 70-85%), OPEX, EBITDA. Negative EBITDA = operating at a loss.
**Burn Metrics**: Gross burn (total spend), net burn (spend minus revenue), remaining cash, months of runway left. Declining runway = burn outpacing revenue growth.
**Balance Sheet**: Cash, AR, total assets, AP, total liabilities, equity. Negative equity is common in early-stage startups with accumulated losses.
""")

tab_saas, tab_pl, tab_burn, tab_bs = st.tabs(["SaaS Metrics", "P&L", "Burn Metrics", "Balance Sheet"])

with tab_saas:
    saas_cols = ["Month", "MRR", "ARR", "Customers", "New Customers", "Churned", "ARPU", "CAC", "LTV", "LTV/CAC", "NRR (%)", "Churn Rate (%)"]
    st.dataframe(full_df[saas_cols].style.format({"MRR": "${:,.0f}", "ARR": "${:,.0f}", "ARPU": "${:,.0f}", "CAC": "${:,.0f}", "LTV": "${:,.0f}", "LTV/CAC": "{:.1f}", "NRR (%)": "{:.1f}%", "Churn Rate (%)": "{:.1f}%"}), use_container_width=True, hide_index=True)

with tab_pl:
    pl_cols = ["Month", "Revenue", "COGS", "Gross Profit", "Gross Margin (%)", "OPEX", "EBITDA", "Net Income"]
    st.dataframe(full_df[pl_cols].style.format({"Revenue": "${:,.0f}", "COGS": "${:,.0f}", "Gross Profit": "${:,.0f}", "Gross Margin (%)": "{:.1f}%", "OPEX": "${:,.0f}", "EBITDA": "${:,.0f}", "Net Income": "${:,.0f}"}), use_container_width=True, hide_index=True)

with tab_burn:
    burn_cols = ["Month", "Gross Burn", "Net Burn", "Cash Balance", "Runway (Months)"]
    st.dataframe(full_df[burn_cols].style.format({"Gross Burn": "${:,.0f}", "Net Burn": "${:,.0f}", "Cash Balance": "${:,.0f}"}), use_container_width=True, hide_index=True)

with tab_bs:
    bs_cols = ["Month", "Cash", "Accounts Receivable", "Other Assets", "Total Assets", "Accounts Payable", "Other Liabilities", "Total Liabilities", "Equity"]
    st.dataframe(full_df[bs_cols].style.format({"Cash": "${:,.0f}", "Accounts Receivable": "${:,.0f}", "Other Assets": "${:,.0f}", "Total Assets": "${:,.0f}", "Accounts Payable": "${:,.0f}", "Other Liabilities": "${:,.0f}", "Total Liabilities": "${:,.0f}", "Equity": "${:,.0f}"}), use_container_width=True, hide_index=True)
st.divider()

# FUNDRAISE PLANNING
st.header("Fundraise Planning")
if net_burn <= 0:
    st.success("You are cash flow positive. Fundraising is strategic, not necessary.")
else:
    target_runway = st.slider("Target Runway After Fundraise (months)", 12, 36, 18)
    fundraise_needed = max(net_burn * target_runway - cash_balance, 0)
    scenarios = []
    for raise_amt in [1_000_000, 2_000_000, 3_000_000, 5_000_000, 8_000_000, 10_000_000]:
        new_cash = cash_balance + raise_amt
        resulting_runway = new_cash / net_burn
        scenarios.append({"Raise Amount": f"${raise_amt:,.0f}", "Post-Raise Cash": f"${new_cash:,.0f}", "Resulting Runway": f"{resulting_runway:.1f} months", "Meets Target": "✅" if resulting_runway >= target_runway else "❌"})
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown(f"""<div style="background:#18181b;border-radius:12px;padding:24px;border:1px solid #27272a;">
            <p style="color:#a1a1aa;font-size:13px;margin:0 0 4px 0;">MINIMUM RAISE NEEDED</p>
            <h2 style="color:#ffffff;margin:0 0 8px 0;">${fundraise_needed:,.0f}</h2>
            <p style="color:#a1a1aa;font-size:13px;margin:0;">To reach {target_runway} months at ${net_burn:,.0f}/mo net burn</p>
        </div>""", unsafe_allow_html=True)
    with col_right:
        st.dataframe(pd.DataFrame(scenarios), use_container_width=True, hide_index=True)
st.divider()

# FOOTER
st.markdown("""
<div style="text-align:center;padding:20px 0;">
    <p style="color:#a1a1aa;font-size:13px;margin:0 0 4px 0;">
        Built by <a href="https://github.com/Shiv290296" style="color:#4ade80;text-decoration:none;">Shivangi Rajat Gaur</a> ·
        <a href="https://github.com/Shiv290296/Cash-Runway-Calculator" style="color:#4ade80;text-decoration:none;">GitHub Repo</a>
    </p>
    <p style="color:#52525b;font-size:12px;margin:0;">For planning purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
