"""
This file is part of the PIConGPU.

Copyright 2022 PIConGPU contributors
Authors: Mika Soren Voss
License: GPLv3+

This test allows verification of the MI. It is irrelevant whether
it is a 2D or 3D simulation. With a 3D simulation, however, attention
must be paid to the Lorentz factor (for more information, see the
bachelor thesis, for example, submitted by Mika Soren Voss).

For information:
    according to the documentation, the case distinction will
    only be incorporated in a later version, which means that
    two cases of KHI currently have to be treated differently.
"""

from scipy.signal import argrelextrema
from scipy.constants import c
import numpy as np
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + "/../../")
import testsuite as ts  # noqa

# general information about the test
title = "distribution"
author = "Mika Soren Voss"

# directory specified
resultDirection = "/bigdata/hplsim/scratch/voss29/myFirst_PIConGPU_runs/picongpu/lib/python/test/setups/test/"
paramDirection = "/bigdata/hplsim/scratch/voss29/myFirst_PIConGPU_runs/runs/thermal/temperature/t=test51/input/include/picongpu/param/"
dataDirection = "/bigdata/hplsim/scratch/voss29/myFirst_PIConGPU_runs/runs/thermal/temperature/t=test51/simOutput/"
openPMDDirection = "/bigdata/hplsim/scratch/voss29/myFirst_PIConGPU_runs/runs/thermal/temperature/t=test51/simOutput/openPMD/"

# parameter information found in .param files
param_Parameter = ["DELTA_T_SI"]
data_Parameter = ["Bz", "step"]
openPMD_Parameter = {"Ex":("E", "x")}

#N_t = len(ts.Reader.openPMDReader.getArray[:,0])
#N_z = len(ts.Reader.openPMDReader.getArray[0,:])
#print(N_t, N_z)
omega_max = 17.6791906440152
k_max = 4183629.101511242

# acceptance, ratio to 1
acceptance = 0.2

# plot data
plot_xlabel = r"$k [1/m]$"
plot_ylabel = r"$\omega / \omega_{pe} $"
# if None or not defined the standard type will be used, see documentation
plot_type = "1D"
# if None or not defined the time will be used
plot_xaxis = None
# for more values see the documentation (e.g. 2D plot needs zaxis and yaxis)


def theory(*args):
    """
    this function indicates how the theoretical values
    can be calculated from the data. Please complete this
    function and use only the theoretical values
    as the return value.
    All parameters that are read from the test-suite must
    be given the same names as in the parameter lists.
    Return:
    -------
    out : theoretical values!
    """
    # gamma is calculated automatically, does not have to be passed
    v = ts.Math.physics.calculateV_O()
    print("theory")
    print((v / (c * np.sqrt(2))))
    return (v / (c * np.sqrt(2)))


def simData(Bz, *args):
    """
    this function indicates how the values from the simulation
    can be calculated from the data. Please complete this
    function and use only the values from the simulation
    as the return value.
    All parameters that are read from the test-suite must
    be given the same names as in the parameter lists.
    Return:
    -------
    out : values from the simulation!
    """
    frequency = ts.Math.physics.plasmafrequence(relativistic=False)
    time = ts.Math.physics.calculateTimeFreq(
                           frequency, step_direction="fields_energy.dat")

    sim_values = ts.Math.math.growthRate(Bz, time)
    sim_values = sim_values[argrelextrema(sim_values, np.less)[0][0]:]
    print("simulation")
    print(sim_values)
    return sim_values