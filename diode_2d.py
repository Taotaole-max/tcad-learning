# Copyright 2013 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

from devsim import set_parameter, solve, write_devices

import devsim.python_packages.simple_physics as simple_physics
import diode_common
#####
# dio2d
#
# Same PN junction physics as diode_1d.py, but meshed in 2D
# (with thin air regions padding the left/right edges).
#

device = "MyDevice"
region = "MyRegion"

diode_common.Create2DMesh(device=device, region=region)

diode_common.SetParameters(device=device, region=region)
set_parameter(device=device, region=region, name="taun", value=1e-8)
set_parameter(device=device, region=region, name="taup", value=1e-8)

diode_common.SetNetDoping(device=device, region=region)

diode_common.InitialSolution(device, region)

# Initial DC solution
solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=30)

diode_common.DriftDiffusionInitialSolution(device, region)
###
### Drift diffusion simulation at equilibrium
###
solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)

####
#### Ramp the bias to 0.5 Volts
####
v = 0.0
while v < 0.51:
    set_parameter(device=device, name=simple_physics.GetContactBiasName("top"), value=v)
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
    simple_physics.PrintCurrents(device, "top")
    simple_physics.PrintCurrents(device, "bot")
    v += 0.1

write_devices(file="diode_2d.dat", type="tecplot")
