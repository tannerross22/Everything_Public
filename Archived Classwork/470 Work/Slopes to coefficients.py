# input: slopes from linear fits (units: eV), volume in Å^3
S_hyd = 449.539968      # fitted slope for hydrostatic: ΔE = S_hyd * delta^2
S_tet = 27.901366     # fitted slope for tetragonal shear
S_shear = 58.132315    # fitted slope for pure shear
V0 = 3.965684**3        # equilibrium cell volume (Å^3)

# unit conversion
eVA3_to_GPa = 160.21766208

# bulk modulus B (eV/Å^3)
B_eVA3 = (2.0/9.0) * (S_hyd / V0)
B_GPa = B_eVA3 * eVA3_to_GPa

# C11 - C12 (eV/Å^3)
X_eVA3 = S_tet / V0

# C44 (eV/Å^3)
C44_eVA3 = S_shear / (2.0 * V0)
C44_GPa = C44_eVA3 * eVA3_to_GPa

# get C11 and C12 (eV/Å^3) from X and B
Y_eVA3 = 3.0 * B_eVA3  # C11 + 2 C12
C12_eVA3 = (Y_eVA3 - X_eVA3) / 3.0
C11_eVA3 = X_eVA3 + C12_eVA3

# convert to GPa
C11_GPa = C11_eVA3 * eVA3_to_GPa
C12_GPa = C12_eVA3 * eVA3_to_GPa

print("Bulk modulus B = {:.3f} GPa".format(B_GPa))
print("C11 = {:.3f} GPa, C12 = {:.3f} GPa, C44 = {:.3f} GPa".format(C11_GPa, C12_GPa, C44_GPa))
