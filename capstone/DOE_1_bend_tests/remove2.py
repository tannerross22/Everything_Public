import matplotlib.pyplot as plt

# ==========================
# PARSER
# ==========================
def parse_sections(filename):
    sections = {}
    current_section = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

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
filename = "Cu_50_1.csv"
sections = parse_sections(filename)

# ❌ Remove bad section
section_to_remove = 2
sections.pop(section_to_remove, None)

plt.figure(figsize=(7.5, 4.5))

displacement_offset = 0.0
new_label = 1  # for clean relabeling

for sec in sorted(sections.keys()):
    disp = sections[sec]["displacement"]
    force = sections[sec]["force"]

    # Apply cumulative offset
    disp_cont = [d + displacement_offset for d in disp]

    plt.plot(disp_cont, force, label=f"Section {new_label}")

    displacement_offset = disp_cont[-1]
    new_label += 1

plt.xlabel("Displacement (mm)")
plt.ylabel("Force (N)")
#plt.title("Flexure Test – Continuous Curve (Bad Section Removed)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()