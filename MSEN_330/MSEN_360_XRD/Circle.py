import matplotlib.pyplot as plt

# Define simple straight-line conceptual data
t = [0, 1, 2, 3, 4, 5]
traditional = [2, 3, 4, 5, 6, 7]  # starts slightly higher, straight line
laser = [3, 3.5, 4, 4.5, 5, 5.5]  # straight line with lower slope

plt.figure(figsize=(10,6))

plt.plot(t, traditional, label="Manual Hardfacing (Cumulative Cost)")
plt.plot(t, laser, label="Automated Laser Hardfacing (Cumulative Cost)")
plt.ylim(0,10)

# Remove numeric tick labels
plt.xticks([])
plt.yticks([])

plt.xlabel("Time", fontsize=20)
plt.ylabel("Cumulative Cost", fontsize=20)

plt.legend(fontsize=24)

plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

# Make all borders black
ax = plt.gca()
ax.set_frame_on(True)
for spine in ax.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

plt.legend()

plt.tight_layout()
plt.show()