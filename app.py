import json
import os
import uuid
from datetime import date, timedelta
from typing import Literal, Optional
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

DATA_FILE = "expenses.json"
CATEGORIES = ["Food", "Transport", "Shopping", "Entertainment", "Other"]


# --- 1. Strict Pydantic Schemas (Batch + Date Validation) ---
class ExtractedExpense(BaseModel):
    title: str = Field(min_length=1, description="Short expense title, e.g., Coffee at Starbucks")
    amount: float = Field(gt=0, description="Numeric expense amount")
    category: Literal["Food", "Transport", "Shopping", "Entertainment", "Other"]
    expense_date: date = Field(description="YYYY-MM-DD date")
    note: str = Field(default="", description="Optional context or details")


class ExpenseBatch(BaseModel):
    expenses: list[ExtractedExpense] = Field(default_factory=list)


# --- 2. Atomic Persistence & Sample Data Helpers ---
def load_expenses() -> list[dict]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            normalized = []
            for item in raw:
                normalized.append({
                    "id": item.get("id", uuid.uuid4().hex[:8]),
                    "title": item.get("title") or item.get("Title", "Untitled"),
                    "amount": round(float(item.get("amount") or item.get("Amount", 0.0)), 2),
                    "category": item.get("category") or item.get("Category", "Other"),
                    "date": item.get("date") or item.get("Date", date.today().isoformat()),
                    "note": item.get("note") if "note" in item else item.get("Note", ""),
                })
            return normalized
        except Exception:
            return []
    return []


def save_expenses(expenses: list[dict]) -> None:
    tmp_file = f"{DATA_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)
    os.replace(tmp_file, DATA_FILE)


def get_sample_expenses() -> list[dict]:
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=5)
    return [
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Coffee at Starbucks",
            "amount": 340.00,
            "category": "Food",
            "date": today.isoformat(),
            "note": "Iced latte and croissant before client sync",
        },
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Kochi Metro & Auto",
            "amount": 115.00,
            "category": "Transport",
            "date": today.isoformat(),
            "note": "Commute to Infopark",
        },
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Lunch at Paragon",
            "amount": 480.00,
            "category": "Food",
            "date": (today - timedelta(days=2)).isoformat(),
            "note": "Team lunch",
        },
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Wireless Mouse & USB-C Hub",
            "amount": 2199.00,
            "category": "Shopping",
            "date": (today - timedelta(days=5)).isoformat(),
            "note": "Work desk accessories",
        },
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Weekend Movie Tickets",
            "amount": 650.00,
            "category": "Entertainment",
            "date": (today - timedelta(days=8)).isoformat(),
            "note": "2 IMAX tickets",
        },
        {
            "id": uuid.uuid4().hex[:8],
            "title": "Previous Month Electricity Bill",
            "amount": 1850.00,
            "category": "Other",
            "date": last_month.isoformat(),
            "note": "KSEB monthly utility bill",
        },
    ]


def get_groq_client() -> Optional[Groq]:
    api_key = os.getenv("GROQ_API_KEY")
    return Groq(api_key=api_key) if api_key else None


# --- 3. LLM Functions (Batch Extraction & Budget-Grounded Summary) ---
def parse_expenses_with_ai(natural_text: str) -> list[dict]:
    client = get_groq_client()
    if not client:
        raise ValueError("GROQ_API_KEY missing in .env")

    today_str = date.today().isoformat()
    prompt = f"""
    Extract one or more personal expenses from the text below into strict JSON.
    Today's date is {today_str}. Resolve relative dates like 'today' or 'yesterday' against {today_str}. If no date is mentioned, use {today_str}.
    Allowed categories: "Food", "Transport", "Shopping", "Entertainment", "Other".
    If the input contains no valid expenses or negative/zero amounts, return {{"expenses": []}}.
    Return ONLY a valid JSON object matching this exact schema:
    {{
      "expenses": [
        {{
          "title": "short title",
          "amount": 100.0,
          "category": "Food",
          "expense_date": "YYYY-MM-DD",
          "note": "optional details or empty string"
        }}
      ]
    }}

    Input: {natural_text}
    """
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    raw_data = json.loads(resp.choices[0].message.content)
    batch = ExpenseBatch(**raw_data)

    return [
        {
            "id": uuid.uuid4().hex[:8],
            "title": item.title.strip(),
            "amount": round(float(item.amount), 2),
            "category": item.category,
            "date": item.expense_date.isoformat(),
            "note": item.note.strip(),
        }
        for item in batch.expenses
    ]


def summarize_expenses_with_ai(
    expenses: list[dict],
    monthly_budget: float,
    current_month_spend: float,
    user_question: str = "",
) -> str:
    client = get_groq_client()
    if not client:
        raise ValueError("GROQ_API_KEY missing in .env")

    filtered_total = sum(e["amount"] for e in expenses)
    by_cat = {}
    for e in expenses:
        by_cat[e["category"]] = round(by_cat.get(e["category"], 0.0) + e["amount"], 2)

    context_payload = {
        "currency": "INR (₹)",
        "monthly_budget_inr": round(monthly_budget, 2),
        "current_month_total_spent_inr": round(current_month_spend, 2),
        "current_month_remaining_budget_inr": round(monthly_budget - current_month_spend, 2),
        "filtered_view_total_inr": round(filtered_total, 2),
        "filtered_category_totals_inr": by_cat,
        "filtered_transactions": expenses[:50],
    }

    task = (
        user_question.strip()
        if user_question.strip()
        else "Provide a concise 3-bullet spending summary, evaluate current month budget pacing, and give 1 actionable saving tip grounded strictly in the verified figures."
    )

    prompt = f"""
    You are a personal finance assistant. Answer ONLY using the verified expense data below.
    Do NOT invent transactions or alter any verified numbers.

    Verified Expense Data:
    {json.dumps(context_payload, indent=2)}

    User Request:
    {task}
    """
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


# --- 4. Streamlit App Setup & Sidebar Controls ---
st.set_page_config(page_title="Personal Expense Tracker", layout="wide")

if "expenses" not in st.session_state:
    st.session_state.expenses = load_expenses()
if "pending_ai_expenses" not in st.session_state:
    st.session_state.pending_ai_expenses = []
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = ""

with st.sidebar:
    st.header("Budget & Demo Controls")
    monthly_budget = st.number_input(
        "Monthly Budget (₹)",
        min_value=500.0,
        max_value=1000000.0,
        value=10000.0,
        step=500.0,
        format="%.2f",
    )
    st.divider()
    st.caption("Quick Demo Utilities")
    if st.button("Load Sample Expenses", use_container_width=True):
        st.session_state.expenses = get_sample_expenses()
        save_expenses(st.session_state.expenses)
        st.session_state.ai_summary = ""
        st.rerun()

    if st.button("Clear All Expenses", use_container_width=True):
        st.session_state.expenses = []
        st.session_state.pending_ai_expenses = []
        st.session_state.ai_summary = ""
        save_expenses([])
        st.rerun()

st.title("Personal Expense Tracker")

# --- 5. AI Quick-Add with Human-in-the-Loop Review & Edge-Case Validation ---
with st.expander("✨ AI Quick-Add (Supports Multiple Expenses & Preview)", expanded=True):
    qcol1, qcol2 = st.columns([4, 1])
    with qcol1:
        ai_text = st.text_input(
            "Describe one or more expenses naturally:",
            placeholder="e.g., Spent 340 on coffee at Starbucks and 120 on an auto ride today",
            label_visibility="collapsed",
        )
    with qcol2:
        extract_clicked = st.button("Extract with AI", use_container_width=True)

    if extract_clicked:
        if not ai_text.strip():
            st.warning("Enter an expense description first.")
        else:
            try:
                with st.spinner("Extracting structured expenses..."):
                    extracted = parse_expenses_with_ai(ai_text)
                    if not extracted:
                        st.warning("No valid expenses detected. Try specifying an item and a positive amount.")
                    else:
                        st.session_state.pending_ai_expenses = extracted
            except Exception as e:
                st.error(f"Could not parse valid expenses from that input ({e}).")

    # Human-in-the-Loop Editable Confirmation Table
    if st.session_state.pending_ai_expenses:
        st.info("Review or edit AI-extracted items before saving:")
        draft_df = pd.DataFrame(st.session_state.pending_ai_expenses)
        edited_df = st.data_editor(
            draft_df[["title", "amount", "category", "date", "note"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "title": st.column_config.TextColumn("Title", required=True),
                "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0.01, format="%.2f", required=True),
                "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True),
                "date": st.column_config.TextColumn("Date (YYYY-MM-DD)", required=True),
                "note": st.column_config.TextColumn("Note"),
            },
            key="ai_draft_editor",
        )
        bcol1, bcol2, _ = st.columns([1.2, 1, 3])
        with bcol1:
            if st.button("Confirm & Save", type="primary", use_container_width=True):
                approved_rows = edited_df.to_dict(orient="records")
                valid_entries = []
                validation_error = None

                for idx, row in enumerate(approved_rows):
                    clean_title = str(row.get("title", "")).strip()
                    clean_date_str = str(row.get("date", "")).strip()
                    try:
                        clean_amount = round(float(row.get("amount", 0)), 2)
                        parsed_date = date.fromisoformat(clean_date_str)
                    except (ValueError, TypeError):
                        validation_error = f"Row {idx + 1}: Invalid date '{clean_date_str}' (must be YYYY-MM-DD) or invalid amount."
                        break

                    if not clean_title:
                        validation_error = f"Row {idx + 1}: Title cannot be empty."
                        break
                    if clean_amount <= 0:
                        validation_error = f"Row {idx + 1}: Amount must be greater than 0."
                        break

                    orig_id = st.session_state.pending_ai_expenses[idx]["id"]
                    valid_entries.append({
                        "id": orig_id,
                        "title": clean_title,
                        "amount": clean_amount,
                        "category": row["category"] if row["category"] in CATEGORIES else "Other",
                        "date": parsed_date.isoformat(),
                        "note": str(row.get("note", "")).strip(),
                    })

                if validation_error:
                    st.error(validation_error)
                else:
                    for entry in reversed(valid_entries):
                        st.session_state.expenses.insert(0, entry)
                    save_expenses(st.session_state.expenses)
                    st.session_state.pending_ai_expenses = []
                    st.rerun()
        with bcol2:
            if st.button("Discard", use_container_width=True):
                st.session_state.pending_ai_expenses = []
                st.rerun()

# --- 6. Manual Input Form ---
with st.form("expense_form", clear_on_submit=True):
    st.subheader("Add Expense Manually")
    col1, col2, col3, col4 = st.columns([2, 1, 1.5, 1.5])
    with col1:
        title = st.text_input("Title *", placeholder="e.g., Coffee at Starbucks")
    with col2:
        amount = st.number_input("Amount (₹) *", min_value=0.0, step=10.0, format="%.2f")
    with col3:
        category = st.selectbox("Category *", options=CATEGORIES)
    with col4:
        expense_date = st.date_input("Date", value=date.today())

    note = st.text_area("Note (Optional)", placeholder="Optional longer text...", height=68)
    submitted = st.form_submit_button("Add Expense", type="primary")

    if submitted:
        if not title.strip():
            st.warning("Please enter a Title.")
        elif amount <= 0:
            st.warning("Amount must be greater than 0.")
        else:
            new_entry = {
                "id": uuid.uuid4().hex[:8],
                "title": title.strip(),
                "amount": round(float(amount), 2),
                "category": category,
                "date": expense_date.isoformat(),
                "note": note.strip(),
            }
            st.session_state.expenses.insert(0, new_entry)
            save_expenses(st.session_state.expenses)
            st.rerun()

# --- 7. Current Month Summary, Filters, Sorted Table & AI Insights ---
expenses = st.session_state.expenses

if not expenses:
    st.info("No expenses recorded yet. Add one above or click 'Load Sample Expenses' in the sidebar!")
else:
    st.divider()
    df = pd.DataFrame(expenses)
    df["date_obj"] = pd.to_datetime(df["date"]).dt.date

    # --- A. Current Month Summary & Budget Guardrail ---
    today = date.today()
    current_month_label = today.strftime("%B %Y")
    month_df = df[
        (pd.to_datetime(df["date"]).dt.year == today.year)
        & (pd.to_datetime(df["date"]).dt.month == today.month)
    ]

    st.subheader(f"Current Month Summary ({current_month_label})")
    month_total = float(month_df["amount"].sum()) if not month_df.empty else 0.0
    month_count = len(month_df)
    month_top_cat = (
        month_df.groupby("category")["amount"].sum().idxmax()
        if not month_df.empty
        else "—"
    )
    remaining_budget = monthly_budget - month_total
    budget_ratio = min(month_total / monthly_budget, 1.0) if monthly_budget > 0 else 0.0

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(f"{current_month_label} Spend", f"₹{month_total:,.2f}")
    mc2.metric("Remaining Budget", f"₹{remaining_budget:,.2f}", delta=f"{(1 - month_total / monthly_budget) * 100:.0f}% left")
    mc3.metric("Transactions", month_count)
    mc4.metric("Top Category", month_top_cat)

    st.progress(budget_ratio, text=f"Monthly Budget Utilization: ₹{month_total:,.2f} / ₹{monthly_budget:,.2f}")
    if month_total > monthly_budget:
        st.error(f"Budget exceeded by ₹{month_total - monthly_budget:,.2f} this month!")

    if not month_df.empty:
        cat_breakdown = (
            month_df.groupby("category", as_index=False)["amount"]
            .sum()
            .sort_values(by="amount", ascending=False)
        )
        with st.expander(f"View {current_month_label} Category Breakdown", expanded=False):
            st.dataframe(
                cat_breakdown,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Total (₹)", format="₹%.2f"),
                },
            )

    st.divider()

    # --- B. Filters (Category, Date Range, Partial Title Match) + Date-Sorted List ---
    st.subheader("All Expenses (Sorted by Date)")
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 1, 1, 1.5])
    with fcol1:
        selected_cats = st.multiselect("Filter by Category", options=CATEGORIES, default=CATEGORIES)
    with fcol2:
        start_date = st.date_input("From Date", value=df["date_obj"].min())
    with fcol3:
        end_date = st.date_input("To Date", value=df["date_obj"].max())
    with fcol4:
        title_search = st.text_input("Search Title (partial match)", placeholder="e.g., coffee, metro...")

    if start_date > end_date:
        st.warning("'From Date' is after 'To Date'. Swap the dates to view matching expenses.")

    filtered_df = df[
        (df["category"].isin(selected_cats))
        & (df["date_obj"] >= start_date)
        & (df["date_obj"] <= end_date)
    ]
    if title_search.strip():
        q = title_search.strip().lower()
        filtered_df = filtered_df[filtered_df["title"].str.lower().str.contains(q, na=False)]

    filtered_df = filtered_df.sort_values(by=["date_obj", "id"], ascending=[False, False])

    if filtered_df.empty:
        st.info("No expenses match your current filter combination. Try widening the date range or selecting more categories.")

    # Filtered Metrics + CSV Download
    fc1, fc2, fc3 = st.columns([1.2, 1.2, 1])
    fc1.metric("Filtered Total", f"₹{filtered_df['amount'].sum():,.2f}")
    fc2.metric("Matching Expenses", len(filtered_df))
    with fc3:
        csv_bytes = filtered_df[["date", "title", "category", "amount", "note"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export Filtered CSV",
            data=csv_bytes,
            file_name="filtered_expenses.csv",
            mime="text/csv",
            use_container_width=True,
        )

    left, right = st.columns([2.2, 1])
    with left:
        st.dataframe(
            filtered_df[["date", "title", "category", "amount", "note"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "Date",
                "title": "Title",
                "category": "Category",
                "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
                "note": "Note",
            },
        )
    with right:
        st.caption("Filtered Spend by Category")
        if not filtered_df.empty:
            st.bar_chart(filtered_df.groupby("category")["amount"].sum())

    # --- C. Grounded AI Summary & Q&A ---
    st.divider()
    st.subheader("AI Spending Summary & Insights")
    scol1, scol2 = st.columns([4, 1])
    with scol1:
        ai_q = st.text_input(
            "Ask a question about your expenses (or leave blank for a full summary):",
            placeholder="e.g., How is my budget pacing this month and where can I cut back?",
            label_visibility="collapsed",
        )
    with scol2:
        gen_summary = st.button("Generate AI Summary", type="primary", use_container_width=True)

    if gen_summary:
        if filtered_df.empty:
            st.warning("No matching expenses to summarize.")
        else:
            try:
                with st.spinner("Analyzing your expenses..."):
                    records = filtered_df[["date", "title", "category", "amount", "note"]].to_dict(orient="records")
                    st.session_state.ai_summary = summarize_expenses_with_ai(
                        records, monthly_budget, month_total, ai_q
                    )
            except Exception as e:
                st.error(f"Summary error: {e}")

    if st.session_state.ai_summary:
        st.info(st.session_state.ai_summary)

    # Delete Single Entry
    with st.expander("Delete an Expense"):
        options = {f"{e['date']} | {e['title']} (₹{e['amount']:.2f})": e["id"] for e in expenses}
        to_delete = st.selectbox("Select entry to remove", options=list(options.keys()))
        if st.button("Delete Selected"):
            del_id = options[to_delete]
            st.session_state.expenses = [e for e in st.session_state.expenses if e["id"] != del_id]
            save_expenses(st.session_state.expenses)
            st.rerun()