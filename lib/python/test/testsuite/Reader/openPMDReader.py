"""
This file is part of the PIConGPU.

Copyright 2022 PIConGPU contributors
Authors: Mika Soren Voss
License: GPLv3+

"""

__all__ = ["OpenPMDReader"]

import os
import testsuite._checkData as cD
import warnings
import numpy as np
import openpmd_api as io
from . import readFiles as rF

class OpenPMDReader(rF.ReadFiles):
    
    def __init__(self, fileExtension: str = r".h5",
                 direction: str = None,
                 directiontype: str = None):
        """
        constructor
        
        Input:
        -------
        fileExtension : str, optional
                        The file extension to search for
                        (e.g. .dat, .param, .json,...)
                        Default: r".h5"
        
        direction :     str, optional
                        Directory of the files, the value from
                        Data.py is used. Must only be set if Data.py is
                        not used or directiontype is not set there
                        Default: None

        directiontype : str, optional
                        Is the designation of the variable in 
                        Data.py for the directory
                        (e.g dataDirection, jsonDirection)
                        Default: None
        
        Raise:
        -------
        TypeError: If neither a directory nor a directiontype was passed
        """
        
        super().__init__(fileExtension, direction, directiontype)
        self.setFileExtionsion(self.__whichFileending())

    def __whichFileending(self) -> str:
        # fixed value, just search for .json, .bp, .h5
        fileExt = r".json"
        fileExt_2 = r".bp"
        fileExt_3 = r".h5"

        if [_ for _ in os.listdir(self._direction) 
            if _.endswith(fileExt)]:
            return r".json"
        elif [_ for _ in os.listdir(self._direction) 
              if _.endswith(fileExt_2)]:
            return r".bp"
        elif [_ for _ in os.listdir(self._direction) 
              if _.endswith(fileExt_3)]:
            return r".h5"
        else:
            raise FileNotFoundError("No .json, .bp or .h5 files could be"
                                    " found in the"
                                    " specified directory. Note: The"
                                    " directory from Data.py may have"
                                    " been used (if Data.py defined).")
            
    def getData(self,
                field: str,
                iteration: int,
                direction: str = "x",
                slice_x: int = None,
                slice_y: int = None,
                slice_z: int = None):
        """
        for reading out individual data or data series (1 dimension)
        using openPMD

        Input:
        -------
        field :      str
                     should be "E" or "B"

        iteration :  int

        direction :  str, optional
                     direction of the field(x, y or z)

        slice_x/slice_y/slice_z : int or str, optional
                     "all" or an integer
                     which data series is to be read out,
                     with "all" the complete data series of the
                     dimension is read out.
                     If all None: half of the data series is accepted
                     Default: None

        Return:
        -------
        d_slice_data : float or list
        """
    
        f_direction = self._direction + "simData_%T" + self._fileExtension

        series = io.Series(f_direction, io.Access.read_only)

        i = series.iterations[iteration]

        # record
        f = i.meshes[field]

        # record components
        f_d = f[direction]
        
        if slice_x is None:
            slice_x = int(f_d.shape[0]/2)
        if slice_y is None:
            slice_y = int(f_d.shape[1]/2)
        if slice_z is None:
            slice_z = int(f_d.shape[2]/2)
            
        if slice_z == "all":
            d_slice_data = f_d[slice_x, slice_y, :]
        elif slice_x == "all":
            d_slice_data = f_d[:, slice_y, slice_z]
        elif slice_y == "all":
            d_slice_data = f_d[slice_x, :, slice_z]
        else:
            d_slice_data = f_d[slice_x, slice_y, slice_z]

        series.flush()
        del series

        return d_slice_data

    def getValues(self,
                  field: str,
                  direction: str = "x",
                  slice_x: int = None,
                  slice_y: int = None,
                  slice_z: int = None):
        """
        returns the value or data series of all iterations as a list
        
        Input:
        -------
        field :      str
                     should be "E" or "B"

        direction :  str, optional
                     direction of the field(x, y or z)

        slice_x/slice_y/slice_z : int or str, optional
                     "all" or an integer
                     which data series is to be read out,
                     with "all" the complete data series of the
                     dimension is read out.
                     If all None: half of the data series is accepted
                     Default: None

        Return:
        -------
        data : ndarray
        """    

        f_direction = self._direction + "simData_%T" + self._fileExtension

        series = io.Series(f_direction, io.Access.read_only)
        
        iterations = series.iterations
        arr = []

        for itera in iterations:
            i = series.iterations[itera]
            f = i.meshes[field]
            f_d = f[direction]
            
            if slice_x is None:
                slice_x = int(f_d.shape[0]/2)
            if slice_y is None:
                slice_y = int(f_d.shape[1]/2)
            if slice_z is None:
                slice_z = int(f_d.shape[2]/2)

            if slice_z == "all":
                d_slice_data = f_d[slice_x, slice_y, :]
            elif slice_x == "all":
                d_slice_data = f_d[:, slice_y, slice_z]
            elif slice_y == "all":
                d_slice_data = f_d[slice_x, :, slice_z]
            else:
                d_slice_data = f_d[slice_x, slice_y, slice_z]
            arr.append(d_slice_data)

        series.flush()
    
        del series
        arr = np.asarray(arr)

        return arr