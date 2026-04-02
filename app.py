from flask import Flask, render_template, request, redirect
import psycopg2
from datetime import datetime

app = Flask(__name__)

# 🔐 PUT YOUR NEW CONNECTION STRING HERE
DB_URL = "postgresql://postgres:HusnCD1f3JUxEJeh@db.umgxrwpetayuzlvsddsw.supabase.co:6543/postgres"

# Categories
INCOME_CATEGORIES = [
    "Salary",
    "Extra Income",
    "Savings Input"
]

EXPENSE_CATEGORIES = [
    "House Repairs",
    "MOT",
    "Car Insurance",
    "Mortgage",
    "Council Tax",
    "Electric & Gas",
    "Water",
    "Food",
    "Fuel",
    "Sundries"
]

# Connect to DB
def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

# Create tables
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            date DATE,
            description TEXT,
            amount NUMERIC,
            category TEXT,
            type TEXT
        )
    ''')

    # Budget table
    c.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id SERIAL PRIMARY KEY,
            month TEXT,
            category TEXT,
            planned NUMERIC,
            type TEXT
        )
    ''')

    conn.commit()
    conn.close()


# Seed budget
def seed_budget():
    conn = get_conn()
    c = conn.cursor()

    current_month = datetime.now().strftime("%Y-%m")

    c.execute("SELECT COUNT(*) FROM budget WHERE month=%s", (current_month,))
    exists = c.fetchone()[0]

    if exists == 0:
        default_budget = [
            ("Salary", 2500, "income"),
            ("Mortgage", 900, "expense"),
            ("Council Tax", 150, "expense"),
            ("Electric & Gas", 200, "expense"),
            ("Water", 50, "expense"),
            ("Food", 300, "expense"),
            ("Fuel", 150, "expense"),
            ("Sundries", 100, "expense")
        ]

        for cat, amount, t in default_budget:
            c.execute('''
                INSERT INTO budget (month, category, planned, type)
                VALUES (%s, %s, %s, %s)
            ''', (current_month, cat, amount, t))

    conn.commit()
    conn.close()


init_db()
seed_budget()


@app.route('/')
def index():
    conn = get_conn()
    c = conn.cursor()

    current_month = datetime.now().strftime("%Y-%m")

    # Transactions
    c.execute("""
        SELECT * FROM transactions
        WHERE TO_CHAR(date, 'YYYY-MM') = %s
        ORDER BY date DESC
    """, (current_month,))
    transactions = c.fetchall()

    # Budget
    c.execute("""
        SELECT category, planned, type FROM budget
        WHERE month=%s
    """, (current_month,))
    budget_rows = c.fetchall()

    budget_data = []

    for cat, planned, t in budget_rows:
        c.execute("""
            SELECT SUM(amount) FROM transactions
            WHERE category=%s AND type=%s AND TO_CHAR(date,'YYYY-MM')=%s
        """, (cat, t, current_month))

        actual = c.fetchone()[0] or 0
        diff = planned - actual

        budget_data.append({
            "category": cat,
            "planned": planned,
            "actual": actual,
            "diff": diff,
            "type": t
        })

    # Income
    c.execute("""
        SELECT SUM(amount) FROM transactions
        WHERE type='income' AND TO_CHAR(date, 'YYYY-MM') = %s
    """, (current_month,))
    income = c.fetchone()[0] or 0

    # Expense
    c.execute("""
        SELECT SUM(amount) FROM transactions
        WHERE type='expense' AND TO_CHAR(date, 'YYYY-MM') = %s
    """, (current_month,))
    expense = c.fetchone()[0] or 0

    balance = income - expense

    conn.close()

    return render_template('index.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        income_categories=INCOME_CATEGORIES,
        expense_categories=EXPENSE_CATEGORIES,
        budget_data=budget_data
    )


@app.route('/add', methods=['POST'])
def add():
    data = request.form

    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        INSERT INTO transactions (date, description, amount, category, type)
        VALUES (%s, %s, %s, %s, %s)
    ''', (
        datetime.now(),
        data['description'],
        data['amount'],
        data['category'],
        data['type']
    ))

    conn.commit()
    conn.close()

    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)