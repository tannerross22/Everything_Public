import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.image as mpimg

# Load the CSV file
data = pd.read_csv('casting_data.csv')

# Load the background image
bg_image = mpimg.imread('Al_Cu_Phase_Diagram.png')  # e.g., 'background.jpg'

# Filter out rows with missing data for composition and the second and third inflection temperatures
filtered_data = data[['Casting composition, Cu wt. %',
                      'First inflection temperature (°C)',
                      'Second inflection temperature (°C)',
                      'Third inflection temperature (°C)']].dropna(subset=['Casting composition, Cu wt. %'])

# Extracting the relevant data for plotting
composition = filtered_data['Casting composition, Cu wt. %']
first_temp = filtered_data['First inflection temperature (°C)']
second_temp = filtered_data['Second inflection temperature (°C)']
third_temp = filtered_data['Third inflection temperature (°C)']

# Creating the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Display the background image
ax.imshow(bg_image, aspect="auto")

# Plotting and connecting the first inflection temperature points
ax.plot(composition, first_temp, 'bo-', label='1st Inflection', markersize=10)

# Plotting and connecting the second inflection temperature points
ax.plot(composition, second_temp, 'go-', label='2nd Inflection', markersize=10)

# Plotting and connecting the third inflection temperature points
ax.plot(composition, third_temp, 'ro-', label='3rd Inflection', markersize=10)

# Adding labels (no title, as requested)
ax.set_xlabel('Casting Composition, Cu wt. %', fontweight='bold')
ax.set_ylabel('Inflection Temperature (°C)', fontweight='bold')

# Customize axis appearance
# Make the axis a square box
ax.tick_params(direction='out', length=6, width=2)  # External tick marks
ax.spines['top'].set_linewidth(2)
ax.spines['right'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)

# Bold tick labels
plt.xticks(fontweight='bold')
plt.yticks(fontweight='bold')

# Removing gridlines
ax.grid(False)

# Show the plot
plt.show()
