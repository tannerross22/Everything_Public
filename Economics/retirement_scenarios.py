import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Your contribution data
yearly_investment = 27_395.36
base_income = 103_000
current_monthly_spending = 5_703.53 * 12  # Your current take-home

# Historical scenarios
scenarios = {
    'Conservative (6%)': 0.06,
    'Historical Average (10%)': 0.10,
    'Optimistic (14%)': 0.14
}

# Current age (assumed 35 - adjust as needed)
current_age = 35

# Calculate portfolio value at different retirement ages
years_range = np.arange(1, 41)
retirement_ages = current_age + years_range

print("=" * 80)
print("RETIREMENT SCENARIOS: Age vs. Annual Spending (4% Rule)")
print("=" * 80)
print(f"\nCurrent Age: {current_age}")
print(f"Current Annual Spending: ${current_monthly_spending:,.2f}")
print(f"Yearly Contribution: ${yearly_investment:,.2f}\n")

# For each scenario, calculate portfolio values and sustainable spending
results_data = []

for scenario_name, annual_return in scenarios.items():
    print(f"\n{scenario_name}")
    print("-" * 80)
    print(f"{'Retirement Age':<20} {'Years Saved':<15} {'Portfolio Value':<20} {'Annual Spending (4%)':<20}")
    print("-" * 80)

    for year in years_range:
        # Calculate portfolio value using FV of annuity formula
        fv = yearly_investment * (((1 + annual_return) ** year - 1) / annual_return)

        # 4% rule: safe annual withdrawal
        annual_spending = fv * 0.04
        retirement_age = current_age + year

        # Only show key milestones
        if year in [5, 10, 15, 20, 25, 30, 35, 40]:
            pct_of_current = (annual_spending / current_monthly_spending) * 100
            print(f"{retirement_age:<20} {year:<15} ${fv:>17,.0f}  ${annual_spending:>17,.0f} ({pct_of_current:>5.0f}% of current)")
            results_data.append({
                'Scenario': scenario_name,
                'Retirement Age': retirement_age,
                'Years': year,
                'Portfolio': fv,
                'Annual Spending': annual_spending
            })

# Create DataFrame for plotting
df = pd.DataFrame(results_data)

# Plot 1: Annual spending vs retirement age
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

for scenario in scenarios.keys():
    scenario_data = df[df['Scenario'] == scenario].sort_values('Retirement Age')
    ax1.plot(scenario_data['Retirement Age'], scenario_data['Annual Spending'],
             marker='o', label=scenario, linewidth=2.5, markersize=6)

ax1.axhline(y=current_monthly_spending, color='red', linestyle='--', linewidth=2, label='Current Spending', alpha=0.7)
ax1.set_xlabel('Retirement Age', fontsize=12)
ax1.set_ylabel('Annual Spending (4% Rule)', fontsize=12)
ax1.set_title('Sustainable Annual Spending by Retirement Age', fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

# Plot 2: Portfolio value vs retirement age
for scenario in scenarios.keys():
    scenario_data = df[df['Scenario'] == scenario].sort_values('Retirement Age')
    ax2.plot(scenario_data['Retirement Age'], scenario_data['Portfolio'],
             marker='o', label=scenario, linewidth=2.5, markersize=6)

ax2.set_xlabel('Retirement Age', fontsize=12)
ax2.set_ylabel('Portfolio Value', fontsize=12)
ax2.set_title('Portfolio Value by Retirement Age', fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M'))

plt.tight_layout()
plt.show()

# Key insights
print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print(f"""
The 4% Rule: You can safely withdraw 4% of your portfolio each year in retirement.
This historically has a 90%+ success rate of lasting 30+ years.

EARLY RETIREMENT (Age 55 - 5 years of work left):
  - Conservative 6%: ${154430.19 * 0.04:,.0f}/year (${154430.19 * 0.04 / 12:,.0f}/month)
  - Average 10%:     ${167251.41 * 0.04:,.0f}/year (${167251.41 * 0.04 / 12:,.0f}/month)

MIDDLE GROUND (Age 57.5 - 10 years of work):
  - Conservative 6%: ${361092.62 * 0.04:,.0f}/year (${361092.62 * 0.04 / 12:,.0f}/month)
  - Average 10%:     ${436611.48 * 0.04:,.0f}/year (${436611.48 * 0.04 / 12:,.0f}/month)

TRADITIONAL (Age 62 - 27 years of work):
  - Conservative 6%: ${2165827.47 * 0.04:,.0f}/year (${2165827.47 * 0.04 / 12:,.0f}/month)
  - Average 10%:     ${4506372.97 * 0.04:,.0f}/year (${4506372.97 * 0.04 / 12:,.0f}/month)

The Trade-off:
  ✓ Working 5 more years (50→55) increases your retirement budget by ~$8K-15K/year
  ✓ Working 10 more years (50→60) increases your retirement budget by ~$35K-70K/year
  ✓ Working 27 years to 62 gets you $180K+ annual spending

  But: Every year you work longer is a year you're NOT in retirement with your health/youth
""")
