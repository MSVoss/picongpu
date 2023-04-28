"""
This file is part of the PIConGPU.

Copyright 2022 PIConGPU contributors
Authors: Mika Soren Voss
License: GPLv3+
"""

from . import dataReader
from . import jsonReader
from . import paramReader
from . import openPMDReader
# from . import cmakeflagReader
import testsuite._checkData as cD


def mainsearch(dataDirection: str = None,
               paramDirection: str = None,
               jsonDirection: str = None,
               openPMDDirection: str = None):

    json = {}
    param = {}
    data = {}
    openPMD = {}
    #dR = dataReader.DataReader(direction=dataDirection,
     #                          directiontype="dataDirection")
    
    # first read jsonParameter
    if (cD.checkExistVariables(variable="jsonDirection") or
            jsonDirection is not None):

        params = cD.checkVariables(variable="json_Parameter")

        jR = jsonReader.JSONReader(direction=jsonDirection,
                                   directiontype="jsonDirection")
        for parameter in params:
            json[parameter] = jR.getValue(parameter)
            
    # read openpmd Parameter
    if (cD.checkExistVariables(variable="openPMDDirection") or
            openPMDDirection is not None):

        openPMDDirection = cD.checkDirection(variable="openPMDDirection",
                                             direction=openPMDDirection)
        #ToDo: fill in the classstructure for openpmd
        params = cD.checkVariables(variable="openPMD_Parameter")
        for parameter in params:
            openPMD[parameter] = openPMDReader.getValue(
                field=params[parameter][0],
                direct = params[parameter][1],
                direction=openPMDDirection)
            
    # read param Parameter
    if (cD.checkExistVariables(variable="paramDirection") or
            paramDirection is not None):

        params = cD.checkVariables(variable="param_Parameter")
        print(cD.checkVariables(variable="param_Parameter"))
        
        pR = paramReader.ParamReader(direction=paramDirection,
                                     directiontype="paramDirection")
        for parameter in params:
            param[parameter] = pR.getValue(parameter)

    # read data values
    if (cD.checkExistVariables(variable="dataDirection") or
            dataDirection is not None):
        params = cD.checkVariables(variable="data_Parameter")
        step_dir = cD.checkVariables(variable="step_direction",
                                     default="")
        if step_dir == "":
            step_dir = None
            
        dR = dataReader.DataReader(direction=dataDirection,
                                   directiontype="dataDirection")

        for parameter in params:
            data[parameter] = dR.getValue(parameter, step_direction=step_dir)

    return json, param, data, openPMD
