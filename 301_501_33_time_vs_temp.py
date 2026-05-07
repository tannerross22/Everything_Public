import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
# Load the datasets from a CSV file
df = pd.read_csv('Eutectic_temp.csv')
plt.rcParams['font.family'] = 'Calibri'
# Extract x1, y1 and x2, y2 from the dataframe
x1 = df['Time']
y1 = df['Temp']

# Create the plot
plt.figure(figsize=(10, 6))

# Plot the first dataset with black dots
plt.plot(x1, y1, color='black', linestyle='-', label="33% Cu")

# Set x and y axis labels
plt.xlabel('Time (s)',fontsize = 24, fontweight='bold')
plt.ylabel('Temperature (C°)',fontsize = 24, fontweight='bold')

# Remove the title and gridlines
plt.title('')  # No title
plt.grid(False)  # No grid

# Set the ticks to be on the outside of the plot box
plt.tick_params(direction='out',labelsize=22, width = 2)
ticks = [0,100,200,300,400]
plt.xticks(ticks)
# Ensure that the bottom of the y-axis starts at exactly 0
plt.ylim(bottom=0)
plt.ylim(top=1000)
plt.xlim(left=0)

for label in plt.gca().get_xticklabels():
    label.set_fontsize(22)  # Set font size
    label.set_fontweight('bold')  # Set font weight to bold

# Set y-tick labels to bold
for label in plt.gca().get_yticklabels():
    label.set_fontsize(22)  # Set font size
    label.set_fontweight('bold')  # Set font weight to bold
# Set the spines (borders) to black and visible on all sides
plt.gca().spines['top'].set_color('black')
plt.gca().spines['right'].set_color('black')
plt.gca().spines['bottom'].set_color('black')
plt.gca().spines['left'].set_color('black')

plt.gca().spines['top'].set_linewidth(1.5)  # Adjust thickness if needed
plt.gca().spines['right'].set_linewidth(1.5)
plt.gca().spines['bottom'].set_linewidth(1.5)
plt.gca().spines['left'].set_linewidth(1.5)
# Show the legend
plt.legend(fontsize=20, loc='upper right', frameon=True, framealpha=1, edgecolor='black')

# Display the plot
plt.show()
