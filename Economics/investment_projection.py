import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Calculate total yearly retirement contributions
base_income = 103_000  # From your screenshot

# 401k contributions
employee_401k = base_income * 0.07  # 7% employee contribution
employer_match_401k = base_income * 0.07  # 7% employer match
total_401k = employee_401k + employer_match_401k

# Roth IRA contribution
roth_contribution = 7_500

# Current investment from budget
monthly_investment = 456.28
current_investment = monthly_investment * 12

# Total yearly investment
yearly_investment = total_401k + roth_contribution + current_investment

print("=" * 60)
print("RETIREMENT SAVINGS PROJECTION ANALYSIS")
print("=" * 60)
print(f"\nYour Base Income: ${base_income:,.2f}")
print(f"\nYearly Contributions:")
print(f"  401k Employee (7%):     ${employee_401k:>12,.2f}")
print(f"  401k Employer Match:    ${employer_match_401k:>12,.2f}")
print(f"  Roth IRA:               ${roth_contribution:>12,.2f}")
print(f"  Current Investment:     ${current_investment:>12,.2f}")
print(f"  " + "-" * 40)
print(f"  TOTAL YEARLY:           ${yearly_investment:>12,.2f}\n")

# Historical S&P 500 returns
# Low: conservative estimate (6% - below average years)
# Average: long-term historical average (10%)
# High: bull market average (14% - above average years)
scenarios = {
    'Conservative (6%)': 0.06,
    'Historical Average (10%)': 0.10,
    'Optimistic (14%)': 0.14
}

years = np.arange(1, 41)  # 1 to 40 years
results = {}

for scenario_name, annual_return in scenarios.items():
    values = []
    for year in years:
        # Future Value of Annuity formula: FV = PMT * [((1 + r)^n - 1) / r]
        # Where PMT = yearly payment, r = annual rate, n = number of years
        fv = yearly_investment * (((1 + annual_return) ** year - 1) / annual_return)
        values.append(fv)
    results[scenario_name] = values

# Create DataFrame for easy viewing
df_results = pd.DataFrame(results, index=years)

# Print key milestones
print("Investment Growth Milestones:")
print("-" * 60)
for year in [5, 10, 20, 30, 40]:
    print(f"\nYear {year}:")
    total_invested = yearly_investment * year
    print(f"  Total Invested: ${total_invested:,.2f}")
    for scenario_name in scenarios.keys():
        total_value = df_results.loc[year, scenario_name]
        gains = total_value - total_invested
        gain_pct = (gains / total_invested) * 100
        print(f"  {scenario_name:30s}: ${total_value:>12,.2f} (Gain: ${gains:>12,.2f} | +{gain_pct:>6.1f}%)")

# Plot the results
plt.figure(figsize=(14, 8))

for scenario_name in scenarios.keys():
    plt.plot(years, results[scenario_name], label=scenario_name, linewidth=2.5)

# Add total invested line for reference
total_invested_line = [yearly_investment * year for year in years]
plt.plot(years, total_invested_line, label='Total Invested', linewidth=2, linestyle='--', color='gray', alpha=0.7)

plt.xlabel('Years', fontsize=12)
plt.ylabel('Portfolio Value ($)', fontsize=12)
plt.title(f'Retirement Savings Growth - ${yearly_investment:,.2f} Annual Contribution\n(401k + Roth + Investment Account)', fontsize=14, fontweight='bold')
plt.legend(fontsize=11, loc='upper left')
plt.grid(True, alpha=0.3)
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M' if x >= 1000000 else f'${x/1000:.0f}K'))

plt.tight_layout()
plt.show()

# Print the data table for reference
print("\n" + "=" * 60)
print("DETAILED PROJECTION TABLE (Every 5 years)")
print("=" * 60)
print(df_results.loc[df_results.index % 5 == 0].to_string(float_format=lambda x: f'${x:,.2f}'))
