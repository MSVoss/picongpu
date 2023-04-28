"""
This file is part of the PIConGPU.

Copyright 2022 PIConGPU contributors
Authors: Mika Soren Voss
License: GPLv3+
"""

import Data
import testsuite.Output.Log as log


def run_testsuite(dataDirection,
                  paramDirection,
                  jsonDirection,
                  resultDirection,
                  openPMDDirection):
    #try:
        # read the Data
        from .Reader import _manager as read

        json, param, data, openPMD = read.mainsearch(dataDirection,
                                                     paramDirection,
                                                     jsonDirection,
                                                     openPMDDirection)

        # now we can determine the theory and simulation
        parameter = {**json, **param, **data, **openPMD}
        print(parameter)
        theory = Data.theory(**parameter)
        simData = Data.simData(**parameter)

        # calculate the deviation
        from .Math import _manager as dv
        max_diff, perc, acc_range, result = dv._calculate(theory, simData)

        # get the result
        from .Output import _manager as output

        output._output(theory=theory,
                       simulation=simData,
                       max_diff=max_diff,
                       perc=perc,
                       acc_range=acc_range,
                       result=result,
                       direction=resultDirection,
                       parameter=parameter)

    #except Exception:
        #log.errorLog()
