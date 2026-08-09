# SPDX-License-Identifier: Apache-2.0
"""
Re-run the 1D PN-junction diode simulation from diode_1d.py, but instead of
just printing currents to the console, keep the intermediate data around so
we can plot:

  1. Carrier density (Electrons/Holes/Donors/Acceptors) vs position, log scale
     -> shows the depletion region and quasi-neutral regions
  2. Electrostatic potential vs position
     -> shows the built-in potential across the junction
  3. I-V curve (top contact current vs bias), log scale
     -> shows the diode's exponential I = I0 * (exp(V/(n*Vt)) - 1) behavior

This is the un-commented, Python-3-fixed version of the matplotlib snippet
that ships (commented out) at the bottom of diode_1d.py.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from devsim import (
    edge_average_model,
    get_edge_model_values,
    get_node_model_values,
    set_parameter,
    solve,
)

import devsim.python_packages.simple_physics as simple_physics
import diode_common

device = "MyDevice"
region = "MyRegion"

diode_common.CreateMesh(device=device, region=region)
diode_common.SetParameters(device=device, region=region)
set_parameter(device=device, region=region, name="taun", value=1e-8)
set_parameter(device=device, region=region, name="taup", value=1e-8)
diode_common.SetNetDoping(device=device, region=region)
diode_common.InitialSolution(device, region)

solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)

diode_common.DriftDiffusionInitialSolution(device, region)
solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)

# ---------------------------------------------------------------------------
# Ramp the bias and record the I-V curve as we go
# ---------------------------------------------------------------------------
voltages = []
top_currents = []

v = 0.0
while v < 0.51:
    set_parameter(device=device, name=simple_physics.GetContactBiasName("top"), value=v)
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)

    electron_current = simple_physics.get_contact_current(
        device=device, contact="top", equation=simple_physics.ece_name
    )
    hole_current = simple_physics.get_contact_current(
        device=device, contact="top", equation=simple_physics.hce_name
    )
    total_current = electron_current + hole_current

    simple_physics.PrintCurrents(device, "top")
    simple_physics.PrintCurrents(device, "bot")

    voltages.append(v)
    top_currents.append(total_current)
    v += 0.1

# ---------------------------------------------------------------------------
# Spatial profiles at the final bias point (0.5 V forward bias)
# ---------------------------------------------------------------------------
x = get_node_model_values(device=device, region=region, name="x")
potential = get_node_model_values(device=device, region=region, name="Potential")
fields = ("Electrons", "Holes", "Donors", "Acceptors")
densities = {
    name: get_node_model_values(device=device, region=region, name=name)
    for name in fields
}

edge_average_model(
    device=device, region=region, node_model="x", edge_model="xmid", average_type="arithmetic"
)
xmid = get_edge_model_values(device=device, region=region, name="xmid")
current_fields = ("ElectronCurrent", "HoleCurrent")
currents = {
    name: get_edge_model_values(device=device, region=region, name=name)
    for name in current_fields
}

# convert x from cm to um for readability
x_um = [xi * 1e4 for xi in x]
xmid_um = [xi * 1e4 for xi in xmid]

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11, 8))

ax = axes[0, 0]
for name in fields:
    ax.semilogy(x_um, [abs(y) + 1 for y in densities[name]], label=name)
ax.set_xlabel("x (um)")
ax.set_ylabel("Density (#/cm^3)")
ax.set_title("Carrier / Doping Density @ V=0.5V")
ax.legend(fontsize=8)

ax = axes[0, 1]
ax.plot(x_um, potential)
ax.set_xlabel("x (um)")
ax.set_ylabel("Potential (V)")
ax.set_title("Electrostatic Potential @ V=0.5V")

ax = axes[1, 0]
for name in current_fields:
    ax.plot(xmid_um, currents[name], label=name)
ax.set_xlabel("x (um)")
ax.set_ylabel("J (A/cm^2)")
ax.set_title("Current Density @ V=0.5V")
ax.legend(fontsize=8)

ax = axes[1, 1]
abs_currents = [abs(i) for i in top_currents]
ax.semilogy(voltages, abs_currents, marker="o")
ax.set_xlabel("Bias V (V)")
ax.set_ylabel("|I_top| (A)")
ax.set_title("I-V Curve (top contact)")

fig.tight_layout()
fig.savefig("diode_1d_plots.png", dpi=150)
print("Saved diode_1d_plots.png")
