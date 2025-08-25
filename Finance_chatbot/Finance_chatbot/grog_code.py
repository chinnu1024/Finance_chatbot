import math
import streamlit as st
import plotly.graph_objects as go
from groq import Groq
import base64

# =====================================
# PAGE CONFIGURATION
# =====================================
st.set_page_config(
    page_title="Personal Finance Q&A (Groq)",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #c5bec2; 
}
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# Example content


# Call this early → replace filename with your asset image
#add_bg_from_local("assets/1.jpeg")  # 👈 change to your file name

# =====================================
# Groq API Configuration
# =====================================
GROQ_API_KEY = "YOUR_API_KEY"   # 🔑 Replace with your key
GROQ_MODEL = "llama-3.1-8b-instant"

# =====================================
# Tax Calculation (Indian New Regime FY 2025-26)
# =====================================
def calculate_tax(annual_income: float) -> float:
    tax = 0
    if annual_income <= 300000:
        return 0
    elif annual_income <= 700000:
        tax = (annual_income - 300000) * 0.05
    elif annual_income <= 1000000:
        tax = (400000 * 0.05) + (annual_income - 700000) * 0.10
    elif annual_income <= 1200000:
        tax = (400000 * 0.05) + (300000 * 0.10) + (annual_income - 1000000) * 0.15
    elif annual_income <= 1500000:
        tax = (400000 * 0.05) + (300000 * 0.10) + (200000 * 0.15) + (annual_income - 1200000) * 0.20
    else:
        tax = (400000 * 0.05) + (300000 * 0.10) + (200000 * 0.15) + (300000 * 0.20) + (annual_income - 1500000) * 0.30
    return tax

# =====================================
# Groq Answer Generation
# =====================================
def generate_answer(query: str, finance_data: dict) -> str:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        context = "\n".join([f"{k}: {v}" for k, v in finance_data.items()])
        prompt = f"""
You are a financial assistant. Use the following user's financial data to answer their questions.

Financial Data:
{context}

Question: {query}

Instructions:
1. Base answers ONLY on the user's financial data.
2. Give practical, simple suggestions.
3. If the data is insufficient, say so clearly.
"""
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful finance assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# =====================================
# Full Pie/Donut Chart Function
# =====================================
def Half_donut_breakdown(categories: dict, total_income: float, 
                         title: str = "Financial Breakdown", currency: str = "₹", hole: float = 0.6):
    total_income = max(0.0, float(total_income))
    labels = list(categories.keys())
    amounts = [max(0.0, float(v)) for v in categories.values()]

    if total_income == 0:
        labels = ["No data"]
        amounts = [1.0]

    percents = [(v / total_income * 100.0) if total_income > 0 else 0.0 for v in amounts]
    customdata = [[amounts[i], percents[i]] for i in range(len(amounts))]

    base_colors = [
        "#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#A66DD4",
        "#FF922B", "#20C997", "#845EC2", "#2C73D2", "#008F7A"
    ]
    colors = [base_colors[i % len(base_colors)] for i in range(len(labels))]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=amounts,
        hole=hole,
        direction="clockwise",
        sort=False,
        marker=dict(colors=colors),
        textinfo="label+percent",
        texttemplate="%{label}<br>%{customdata[1]:.1f}%",
        customdata=customdata,
        hovertemplate=f"%{{label}}<br>{currency}%{{customdata[0]:,.0f}}"
                      f"<br>%{{customdata[1]:.2f}}% of income<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        margin=dict(l=10, r=10, t=60, b=10),
        showlegend=False,
        height=420,
    )

    return fig

# =====================================
# STREAMLIT UI
# =====================================
def main():
    st.markdown('<h1 style="text-align:center;color:#1E88E5;">💰 Personal Finance Chatbot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#546E7A;">Enter your financial details and ask questions </p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configuration")
        st.success("🚀 Using Groq API")
        st.info(f"Model: {GROQ_MODEL}")
        st.divider()
        st.markdown("""
        ### ℹ️ How it works
        1. Enter financial details (income, expenses, PF%, investments, etc.)
        2. Tax is calculated automatically using Indian slabs
        3. Savings are auto-calculated
        4. Visual gauges show financial health
        5. Ask questions about your finances
        """)

    # Collect Finance Data
    st.header("📊 Enter Your Financial Data")
    monthly_income = st.number_input("Monthly Income (₹)", min_value=0, step=1000)
    rent = st.number_input("Rent / Housing (₹)", min_value=0, step=500)
    food = st.number_input("Food / Groceries (₹)", min_value=0, step=500)
    transport = st.number_input("Transport (₹)", min_value=0, step=500)
    pf_percent = st.number_input("Provident Fund (PF) % of Income", min_value=0, max_value=100, step=1)
    investment = st.number_input("Investments (₹)", min_value=0, step=500)
    other_expenses = st.number_input("Other Expenses (₹)", min_value=0, step=500)

    pf = (monthly_income * pf_percent) / 100

    annual_income = monthly_income * 12
    annual_tax = calculate_tax(annual_income)
    monthly_tax = annual_tax / 12 if annual_tax > 0 else 0

    total_expenses = rent + food + transport + pf + investment + other_expenses + monthly_tax
    savings = monthly_income - total_expenses

    finance_data = {
        "Monthly Income": f"₹{monthly_income}",
        "Provident Fund (PF)": f"₹{pf:.2f} ({pf_percent}%)",
        "Income Tax (Monthly)": f"₹{monthly_tax:.2f}",
        "Investments": f"₹{investment}",
        "Other Expenses": f"₹{other_expenses}",
        "Total Expenses": f"₹{total_expenses:.2f}",
        "Net Savings": f"₹{savings:.2f}",
    }

    breakdown_data = {
        "Rent": rent,
        "Food": food,
        "Transport": transport,
        "PF": pf,
        "Investments": investment,
        "Other Expenses": other_expenses,
        "Tax": monthly_tax,
        "Savings": savings
    }

    # ==============================
    # Display Summary and Pie Chart Side by Side
    # ==============================
    st.subheader("📊 Financial Overview")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**Calculated Summary**")
        for k, v in finance_data.items():
            st.write(f"**{k}:** {v}")

    with col2:
        st.plotly_chart(
            Half_donut_breakdown(breakdown_data, total_income=monthly_income, 
                                 title="Monthly Breakdown (% of Income)"),
            use_container_width=True
        )

    # ==============================
    # Q&A at the bottom
    # ==============================
    st.header("💬 Ask a Question")
    query = st.text_area("Ask anything:", placeholder="Example: How much should I invest more to improve savings?")
    if st.button("➤", disabled=not query):
        with st.spinner("Analyzing your financial data..."):
            answer = generate_answer(query, finance_data)
            st.success("✅ Answer found!")
            st.write(answer)

if __name__ == "__main__":
    main()

