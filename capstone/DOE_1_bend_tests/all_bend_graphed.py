import matplotlib.pyplot as plt
import glob
import os

# ==========================
# PARSER
# ==========================
def parse_sections(filename):
    sections = {}
    current_section = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            # Detect section header
            if line and line[0].isdigit() and ",Time," in line:
                current_section = int(line.split(",")[0])
                sections[current_section] = {"disp": [], "force": []}
                continue

            if current_section is None:
                continue

            # Data rows
            if line.startswith('"",'):
                parts = line.replace('"', "").split(",")

                try:
                    d = float(parts[2])   # displacement (mm)
                    F = float(parts[3])   # force (N)
                except:
                    continue

                sections[current_section]["disp"].append(d)
                sections[current_section]["force"].append(F)

    return sections


# ==========================
# BUILD CONTINUOUS CURVE
# ==========================
def build_curve(sections):

    displacement_offset = 0

    disp_all = []
    force_all = []

    for sec in sorted(sections.keys()):

        disp = sections[sec]["disp"]
        force = sections[sec]["force"]

        disp_cont = [d + displacement_offset for d in disp]

        disp_all.extend(disp_cont)
        force_all.extend(force)

        displacement_offset = disp_cont[-1]

    return disp_all, force_all


# ==========================
# MAIN
# ==========================
plt.figure(figsize=(8,6))

files = glob.glob("*.csv")

for file in files:

    sections = parse_sections(file)

    # Remove bad section for specific file
    if os.path.basename(file) == "Cu_50_1.csv":
        sections.pop(2, None)

    disp, force = build_curve(sections)

    label = os.path.splitext(os.path.basename(file))[0]

    plt.plot(disp, force, label=label)


plt.xlabel("Displacement (mm)")
plt.ylabel("Force (N)")
plt.title("Flexure Test Comparison (Force–Displacement)")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.show()