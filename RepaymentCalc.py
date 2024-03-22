import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.graph_objs as go
import pandas as pd

# Function to calculate write-off year based on the plan and first loan payment year
def calculate_write_off_year(plan, first_loan_year):
    if plan in ["Plan 1", "Plan 4"]:
        if first_loan_year >= 2006:
            return 25 + first_loan_year
        else:  # If the first loan was paid before 2006
            return first_loan_year + 65
    elif plan == "Plan 2":
        return 30 + first_loan_year
    elif plan == "Plan 5":
        return 40 + first_loan_year
    elif plan == "Postgraduate Loan":
        return 30 + first_loan_year  

# Function to get the annual interest rate for each plan
def get_annual_interest_rate(plan):
    rates = {
        "Plan 1": 0.0625,
        "Plan 2": 0.077,
        "Plan 4": 0.0625,
        "Plan 5": 0.077,
        "Postgraduate Loan": 0.077  # Assuming the same rate as Plan 2 for simplicity
    }
    return rates.get(plan, 0)

# Function to calculate the annual repayment based on the plan and salary
def calculate_annual_repayment(plan, salary):
    thresholds = {
        "Plan 1": 22015,
        "Plan 2": 27295,
        "Plan 4": 27660,
        "Plan 5": 25000,
        "Postgraduate Loan": 21000  # Hypothetical threshold
    }
    rate = 0.09  # 9%
    threshold = thresholds.get(plan, 0)
    if salary > threshold:
        return (salary - threshold) * rate
    return 0

# Helper function to calculate the loan balance over time, considering salary changes
def calculate_loan_balance_with_salary_changes(loan_amount, start_year, write_off_year, initial_salary, salary_changes, annual_interest_rate):
    current_salary = initial_salary
    loan_balance = [loan_amount]
    years = np.arange(start_year, write_off_year + 1)
    for year in years[1:]:
        if year in salary_changes:
            current_salary = salary_changes[year]
        if loan_balance[-1] <= 0:
            break
        annual_repayment = calculate_annual_repayment(plan_option, current_salary)
        interest_for_year = loan_balance[-1] * annual_interest_rate
        new_balance = loan_balance[-1] + interest_for_year - annual_repayment
        new_balance = max(0, new_balance)  # Ensure balance does not go negative
        loan_balance.append(new_balance)
    return years[:len(loan_balance)], loan_balance


# Initialize or update the session state for salary changes
if 'salary_changes' not in st.session_state:
    st.session_state.salary_changes = []

# Function to add a new salary change entry
def add_salary_change():
    st.session_state.salary_changes.append({'year': new_year, 'salary': new_salary})

# Function to remove a salary change entry
def remove_salary_change(index):
    st.session_state.salary_changes.pop(index)
    
    
# Streamlit UI for inputs and dynamic salary change management
st.title("UK Student Loan Repayment Calculator")
with st.expander("How to determine what plan you are on"):
    st.markdown("""
    **If you applied to Student Finance England, the repayment plan you’re on depends on when you started your course and what type of course you studied.**

    - **If you started your course on or after 1 August 2023:**
        - You’ll be on **Plan 5** if:
            - You’re studying an undergraduate course.
            - You’re studying a Postgraduate Certificate of Education (PGCE).
            - You take out an Advanced Learner Loan.
        - You’ll be on a **Postgraduate Loan plan** if you’re studying a postgraduate master’s or doctoral course.
        - You’ll be on **Plan 2** if you take out a Higher Education Short Course Loan.

    - **If you started your course between 1 September 2012 and 31 July 2023:**
        - You’ll be on **Plan 2** if:
            - You’re studying an undergraduate course.
            - You’re studying a Postgraduate Certificate of Education (PGCE).
            - You take out an Advanced Learner Loan.
            - You take out a Higher Education Short Course Loan.
        - You’ll be on a **Postgraduate Loan plan** if you’re studying a postgraduate master’s or doctoral course.

    - **If you started your course before 1 September 2012:**
        - You’re on **Plan 1**.
    """)
st.write("Interest rates are subject to change according to the Bank of England's rate.")

# Initialize or update the session state for salary changes
if 'salary_changes' not in st.session_state:
    st.session_state.salary_changes = []

plan_option = st.selectbox("Select Your Student Loan Plan", 
                           ("Plan 1", "Plan 2", "Plan 4", "Plan 5", "Postgraduate Loan"))
first_loan_year = st.number_input("First Loan Payment Year", min_value=1980, 
                                  value=2010)
loan_amount = st.number_input("Total Loan Balance in thousands (£)", min_value=0, value=50, format = "%d") * 1000  # Input in 'k', convert to full amount
initial_salary = st.number_input("Current Annual Salary in thousands", min_value=0, value=35, format = "%d")  # Input as 'k'

# Function to add a new salary change entry
def add_salary_change(year, salary):
    st.session_state.salary_changes.append({'year': year, 'salary': salary * 1000})  # Convert 'k' to full amount

# Function to remove a salary change entry
def remove_salary_change(index):
    st.session_state.salary_changes.pop(index)

# UI to add salary changes
st.write("Here you can enter future earnings predictions to see how this affects the loan balance over time")
with st.form("salary_changes_form"):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        new_year = st.number_input("Year of Change", min_value=first_loan_year+1, key="new_year")
    with col2:
        new_salary = st.number_input("New Salary in thousands", key="new_salary", format = "%d",min_value = initial_salary)
    submitted = st.form_submit_button("Add Salary Change")
    if submitted:
        add_salary_change(new_year, new_salary)

# Display and manage current salary changes
if st.session_state.salary_changes:
    for i, change in enumerate(st.session_state.salary_changes):
        st.write(f"Year: {change['year']}, New Salary: £{change['salary']/1000}k")
        st.button("Remove", key=f"remove_{i}", on_click=remove_salary_change, args=(i,))

# Convert session state salary changes for calculations
salary_changes_dict = {change['year']: change['salary'] for change in st.session_state.salary_changes}

# Perform calculations
write_off_year = calculate_write_off_year(plan_option, first_loan_year)
annual_interest_rate = get_annual_interest_rate(plan_option)
years, loan_balance = calculate_loan_balance_with_salary_changes(
    loan_amount, first_loan_year, write_off_year, initial_salary*1000, salary_changes_dict, annual_interest_rate)  # Convert initial salary from 'k' to full amount

# Plotting with matplotlib
fig, ax = plt.subplots()
ax.plot(years, loan_balance, label='Loan Balance', marker='o', linestyle='-')

for year in salary_changes_dict:
    ax.axvline(x=year, color='red', linestyle='--')  # Mark salary changes

ax.axvline(x=write_off_year, color='green', linestyle='--', label='Write-off Year')  # Highlight write-off year

ax.set_xlabel('Year')
ax.set_ylabel('Loan Balance (£)')
ax.set_title('Projected Student Loan Balance Over Time')
ax.legend()

plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)