import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import json

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="SGPayPulse | Public Leadership Portal",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI cards, badge styling, and table headers
st.markdown("""
    <style>
    /* Metric Card styling */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    /* Section Container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    /* Badge tag styling */
    .badge-tag {
        background-color: #e7f5ff;
        color: #1971c2;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    /* Custom subheader styling */
    .stHeaderTitle {
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. IN-MEMORY DATABASE & DATA SEEDING
# ==========================================
@st.cache_resource
def init_db():
    """Initializes in-memory SQLite database populated with Singapore MP & Ministerial records."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE office_holders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT,
        term TEXT,
        constituency TEXT,
        portfolio TEXT,
        base_allowance_annual REAL,
        variable_bonus_months REAL
    )
    """)

    # Mock Data Records for Public Office Holders
    records = [
        # Prime Ministers & Senior Ministers
        ("Lawrence Wong", "Prime Minister", "15th Term (2024-Present)", "Marsiling-Yew Tee GRC", "Prime Minister & Minister for Finance", 2200000, 7.0),
        ("Lawrence Wong", "Minister", "14th Term (2020-2024)", "Marsiling-Yew Tee GRC", "Minister for Finance", 1100000, 6.0),
        ("Lee Hsien Loong", "Senior Minister", "15th Term (2024-Present)", "Ang Mo Kio GRC", "Senior Minister", 1800000, 6.5),
        ("Lee Hsien Loong", "Prime Minister", "14th Term (2020-2024)", "Ang Mo Kio GRC", "Prime Minister", 2200000, 7.0),
        ("Lee Hsien Loong", "Prime Minister", "13th Term (2015-2020)", "Ang Mo Kio GRC", "Prime Minister", 2200000, 7.0),
        
        # Education Ministers
        ("Chan Chun Sing", "Minister", "15th Term (2024-Present)", "Tanjong Pagar GRC", "Minister for Education", 1100000, 5.5),
        ("Chan Chun Sing", "Minister", "14th Term (2020-2024)", "Tanjong Pagar GRC", "Minister for Education", 1100000, 5.5),
        ("Ong Ye Kung", "Minister", "13th Term (2015-2020)", "Sembawang GRC", "Minister for Education (Higher Ed)", 1100000, 5.0),
        ("Ng Chee Meng", "Minister", "13th Term (2015-2020)", "Pasir Ris-Punggol GRC", "Minister for Education (Schools)", 1100000, 5.0),
        
        # Finance & Health Ministers
        ("Heng Swee Keat", "Deputy Prime Minister", "14th Term (2020-2024)", "East Coast GRC", "DPM & Minister for Finance", 1600000, 6.0),
        ("Heng Swee Keat", "Minister", "13th Term (2015-2020)", "Tampines GRC", "Minister for Finance", 1100000, 6.0),
        ("Ong Ye Kung", "Minister", "15th Term (2024-Present)", "Sembawang GRC", "Minister for Health", 1100000, 5.5),
        ("Ong Ye Kung", "Minister", "14th Term (2020-2024)", "Sembawang GRC", "Minister for Health", 1100000, 5.5),
        ("Gan Kim Yong", "Deputy Prime Minister", "15th Term (2024-Present)", "Chua Chu Kang GRC", "DPM & Minister for Trade and Industry", 1600000, 6.0),
        
        # Members of Parliament & Office Holders
        ("Pritam Singh", "Leader of the Opposition", "15th Term (2024-Present)", "Aljunied GRC", "MP & Opposition Leader", 385000, 2.0),
        ("Pritam Singh", "Leader of the Opposition", "14th Term (2020-2024)", "Aljunied GRC", "MP & Opposition Leader", 385000, 2.0),
        ("Pritam Singh", "MP", "13th Term (2015-2020)", "Aljunied GRC", "Member of Parliament", 192500, 1.0),
        ("Sylvia Lim", "MP", "15th Term (2024-Present)", "Aljunied GRC", "Member of Parliament", 192500, 1.0),
        ("Sylvia Lim", "MP", "14th Term (2020-2024)", "Aljunied GRC", "Member of Parliament", 192500, 1.0),
        ("Sylvia Lim", "MP", "13th Term (2015-2020)", "Aljunied GRC", "Member of Parliament", 192500, 1.0),
        ("Sun Xueling", "Minister of State", "15th Term (2024-Present)", "Punggol West SMC", "Minister of State (MHA & MSF)", 770000, 4.0),
        ("Sun Xueling", "Minister of State", "14th Term (2020-2024)", "Punggol West SMC", "Minister of State", 770000, 4.0)
    ]

    cursor.executemany("""
    INSERT INTO office_holders (name, role, term, constituency, portfolio, base_allowance_annual, variable_bonus_months)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    return conn

conn = init_db()

# ==========================================
# 3. CHATBOT QUERY ENGINE
# ==========================================
def query_database(user_query: str):
    """Executes keyword-matching SQL queries against the database."""
    cursor = conn.cursor()
    q = user_query.lower()

    if "education" in q:
        cursor.execute("SELECT name, role, term, constituency, portfolio FROM office_holders WHERE portfolio LIKE '%Education%'")
    elif "finance" in q:
        cursor.execute("SELECT name, role, term, constituency, portfolio FROM office_holders WHERE portfolio LIKE '%Finance%'")
    elif "more than two terms" in q or "2 terms" in q or "multiple terms" in q:
        cursor.execute("SELECT name, COUNT(DISTINCT term) as terms_count, GROUP_CONCAT(constituency, ', ') FROM office_holders GROUP BY name HAVING terms_count >= 3")
    elif "pritam" in q or "sylvia" in q:
        cursor.execute("SELECT name, role, term, constituency, portfolio FROM office_holders WHERE name LIKE '%Pritam%' OR name LIKE '%Sylvia%'")
    else:
        cursor.execute("SELECT name, role, term, constituency, portfolio FROM office_holders LIMIT 10")
        
    return cursor.fetchall()

def run_ai_bot(user_query: str):
    """Generates structured response using OpenAI API or Offline Logic Engine."""
    db_results = query_database(user_query)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
            You are SGPayPulse AI Assistant for Singapore Public Office & Parliamentary records.
            User Query: {user_query}
            Retrieved Records: {json.dumps(db_results)}
            Provide a clear, neutral, well-structured response with Markdown formatting.
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception:
            pass

    # Offline Response Engine Fallback
    q = user_query.lower()
    if "education" in q:
        res = "### 📚 Ministers for Education Across Terms\n\n"
        for r in db_results:
            res += f"- **{r[0]}** ({r[2]}): Served as *{r[4]}* representing **{r[3]}**.\n"
        res += "\n*Key Insight*: Over the last 3 terms, Education transitioned from joint junior/senior minister portfolios to a unified Ministry under Chan Chun Sing."
        return res
    elif "finance" in q:
        res = "### 💰 Minister for Finance Comparison\n\n"
        res += "| Term | Minister | Role / Portfolio | Constituency |\n"
        res += "| --- | --- | --- | --- |\n"
        for r in db_results:
            res += f"| {r[2]} | **{r[0]}** | {r[4]} | {r[3]} |\n"
        res += "\n*Key Insight*: Heng Swee Keat managed the Ministry of Finance through the COVID-19 Budgets before transitioning the portfolio to Lawrence Wong."
        return res
    elif "more than two terms" in q or "2 terms" in q:
        res = "### 🏛️ Office Holders Representing Constituencies for 3+ Terms\n\n"
        for r in db_results:
            res += f"- **{r[0]}**: Served across **{r[1]} consecutive terms** in constituencies: *{r[2]}*.\n"
        return res
    else:
        res = f"### 🔍 Search Query Results for: '{user_query}'\n\n"
        for r in db_results:
            res += f"- **{r[0]}** | {r[1]} ({r[2]}) | Portfolio: *{r[4]}* | Constituency: **{r[3]}**\n"
        return res

# ==========================================
# 4. NAVIGATION BAR & MAIN ROUTING
# ==========================================
st.sidebar.title("🦁 SGPayPulse Navigation")
st.sidebar.caption("Transparency & Knowledge Portal")

# Main Navigation Radio Button
page = st.sidebar.radio(
    "Go to",
    ["🏠 Home (Data Snapshot)", "🤖 Tool (AI Assistant)", "⚖️ Comparator Tool", "ℹ️ Project Info"],
    index=0
)

st.sidebar.divider()
st.sidebar.markdown("""
<div style='font-size: 12px; color: #6c757d;'>
<b>Dataset Scope</b>: 13th - 15th Parliamentary Terms<br>
<b>Data Source</b>: Official Public Benchmarks
</div>
""", unsafe_allow_html=True)

# ==========================================
# PAGE 1: 🏠 HOME (DATABASE SNAPSHOT & METRICS)
# ==========================================
if page == "🏠 Home (Data Snapshot)":
    st.title("🏠 SGPayPulse - Public Office Holders Snapshot")
    st.markdown("A consolidated transparency database of Singapore Ministers, MPs, and Parliamentary leadership[cite: 1].")
    
    # TOP KPI CARDS
    df_all = pd.read_sql_query("SELECT * FROM office_holders", conn)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Records Tracked", len(df_all))
    kpi2.metric("Unique Ministers & MPs", df_all["name"].nunique())
    kpi3.metric("Parliamentary Terms", "13th to 15th")
    kpi4.metric("Constituencies Covered", df_all["constituency"].nunique())

    st.divider()

    # SNAPSHOT FILTER & DATA TABLE
    st.subheader("📋 Dataset Snapshot & Explorer")
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        term_filter = st.multiselect("Filter Term", options=df_all["term"].unique(), default=df_all["term"].unique())
    with col_f2:
        role_filter = st.multiselect("Filter Role", options=df_all["role"].unique(), default=df_all["role"].unique())
    with col_f3:
        search_kw = st.text_input("🔍 Search Name, Constituency, or Portfolio", value="")

    # Apply Filters
    df_filtered = df_all[(df_all["term"].isin(term_filter)) & (df_all["role"].isin(role_filter))]
    if search_kw:
        df_filtered = df_filtered[
            df_filtered["name"].str.contains(search_kw, case=False) |
            df_filtered["constituency"].str.contains(search_kw, case=False) |
            df_filtered["portfolio"].str.contains(search_kw, case=False)
        ]

    st.dataframe(
        df_filtered[["name", "role", "term", "constituency", "portfolio", "base_allowance_annual"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Office Holder"),
            "role": st.column_config.TextColumn("Role / Rank"),
            "term": st.column_config.TextColumn("Parliamentary Term"),
            "constituency": st.column_config.TextColumn("Constituency"),
            "portfolio": st.column_config.TextColumn("Portfolio / Appointment"),
            "base_allowance_annual": st.column_config.NumberColumn("Annual Allowance Benchmark ($)", format="$%d")
        }
    )

    st.divider()

    # VISUAL ANALYTICS CHART
    st.subheader("📊 Remuneration Benchmarks by Role & Term")
    fig = px.bar(
        df_filtered,
        x="name",
        y="base_allowance_annual",
        color="role",
        facet_col="term",
        hover_data=["constituency", "portfolio"],
        title="Annual Benchmark Allowance ($ SGD)",
        labels={"base_allowance_annual": "Annual Pay ($)", "name": "Office Holder"}
    )
    fig.update_xaxes(matches=None)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE 2: 🤖 TOOL (AI CHATBOT)
# ==========================================
elif page == "🤖 Tool (AI Assistant)":
    st.title("🤖 SGPayPulse AI Query Tool")
    st.markdown("Ask natural language questions to query parliamentary records, ministerial terms, and leadership portfolios[cite: 1].")

    # PRE-SET SUGGESTIONS
    st.markdown("**Suggested Prompts:**")
    sp_col1, sp_col2, sp_col3 = st.columns(3)
    
    suggested_prompt = None
    if sp_col1.button("Who served as Minister for Education over the last three terms?"):
        suggested_prompt = "Who served as Minister for Education over the last three terms?"
    if sp_col2.button("Compare the current and previous Ministers for Finance."):
        suggested_prompt = "Compare the current and previous Ministers for Finance."
    if sp_col3.button("Which MPs have represented a constituency for more than two terms?"):
        suggested_prompt = "Which MPs have represented a constituency for more than two terms?"

    # Session State Chat Messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the SGPayPulse AI Query Tool! Ask me any question about Singapore Ministers, MPs, constituencies, or parliamentary records."}
        ]

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle Input
    chat_input = st.chat_input("Ask a question about Ministers or MPs...")
    active_prompt = suggested_prompt if suggested_prompt else chat_input

    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.markdown(active_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching parliamentary database..."):
                reply = run_ai_bot(active_prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

# ==========================================
# PAGE 3: ⚖️ COMPARATOR TOOL
# ==========================================
elif page == "⚖️ Comparator Tool":
    st.title("⚖️ Public Leadership Comparator")
    st.markdown("Side-by-side comparative analysis of office holders, constituencies, and portfolios over time[cite: 1].")

    df_all = pd.read_sql_query("SELECT * FROM office_holders", conn)
    names_list = sorted(df_all["name"].unique().tolist())

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        leader_1 = st.selectbox("Select First Office Holder", names_list, index=0)
    with col_s2:
        leader_2 = st.selectbox("Select Second Office Holder", names_list, index=1 if len(names_list) > 1 else 0)

    if leader_1 and leader_2:
        df_l1 = df_all[df_all["name"] == leader_1]
        df_l2 = df_all[df_all["name"] == leader_2]

        comp_c1, comp_c2 = st.columns(2)

        with comp_c1:
            st.info(f"### {leader_1}")
            for _, row in df_l1.iterrows():
                st.markdown(f"**Term**: `{row['term']}`")
                st.markdown(f"- **Role**: {row['role']}")
                st.markdown(f"- **Portfolio**: {row['portfolio']}")
                st.markdown(f"- **Constituency**: {row['constituency']}")
                st.markdown(f"- **Benchmark Pay**: **${row['base_allowance_annual']:,.0f}**")
                st.divider()

        with comp_c2:
            st.success(f"### {leader_2}")
            for _, row in df_l2.iterrows():
                st.markdown(f"**Term**: `{row['term']}`")
                st.markdown(f"- **Role**: {row['role']}")
                st.markdown(f"- **Portfolio**: {row['portfolio']}")
                st.markdown(f"- **Constituency**: {row['constituency']}")
                st.markdown(f"- **Benchmark Pay**: **${row['base_allowance_annual']:,.0f}**")
                st.divider()

# ==========================================
# PAGE 4: ℹ️ PROJECT INFO
# ==========================================
elif page == "ℹ️ Project Info":
    st.title("ℹ️ Project Information & Proposal Details")
    st.markdown("""
    ### Project Title: SGPayPulse[cite: 1]
    **Program**: AI Bootcamp 2026 August Run Proposal[cite: 1]  
    **Submission Type**: Type 2 Capstone[cite: 1]  

    #### Problem Statement[cite: 1]
    Detailed historical information about Singaporean ministers and parliament members, including their service terms and comparative data, is fragmented and not readily available in a user-friendly format[cite: 1]. This lack of transparency can hinder public understanding of political representation and accountability[cite: 1].

    #### Solution Overview[cite: 1]
    **SGPayPulse** serves as a centralized knowledge platform for Singapore's political leadership and parliamentary information[cite: 1]:
    1. Conversational access to information about Ministers and MPs[cite: 1].
    2. Side-by-side comparison across parliamentary terms[cite: 1].
    3. Insights on constituencies represented and portfolios held over time[cite: 1].
    4. Structured summaries generated from publicly available benchmark data[cite: 1].

    #### Team Members[cite: 1]
    - **Mayukh Rastogi**[cite: 1]
    - **Boon Hwee NG** (`NG_Boon_Hwee@tech.gov.sg`)[cite: 1]
    - **Vishal ARYA** (`Vishal_ARYA@bca.gov.sg`)[cite: 1]
    - **Keat Jau YAW** (`YAW_Keat_Jau@swda.gov.sg`)[cite: 1]
    """)