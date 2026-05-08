import matplotlib.pyplot as plt

def parse_sections(filename):
    sections = {}
    current_section = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            # Detect section header
            if line and line[0].isdigit() and ",Time," in line:
                current_section = int(line.split(",")[0])
                sections[current_section] = {
                    "displacement": [],
                    "force": []
                }
                continue

            if current_section is None:
                continue

            if line.startswith('"",'):
                parts = line.replace('"', "").split(",")

                try:
                    displacement = float(parts[2])
                    force = float(parts[3])
                except (IndexError, ValueError):
                    continue

                sections[current_section]["displacement"].append(displacement)
                sections[current_section]["force"].append(force)

    return sections


# ==========================
# MAIN
# ==========================

filename = "60_70_1.csv"
sections = parse_sections(filename)

plt.figure(figsize=(7.5, 4.5))

displacement_offset = 0.0

for sec in sorted(sections.keys()):
    disp = sections[sec]["displacement"]
    force = sections[sec]["force"]

    # Apply cumulative offset
    disp_continuous = [d + displacement_offset for d in disp]

    plt.plot(disp_continuous, force, label=f"Section {sec}")

    # Update offset to last displacement of this section
    displacement_offset = disp_continuous[-1]

plt.xlabel("Displacement (mm)")
plt.ylabel("Force (N)")
#plt.title("Flexure Test – Continuous Displacement Reconstruction")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()