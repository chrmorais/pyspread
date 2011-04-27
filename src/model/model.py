#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2008 Martin Manns
# Distributed under the terms of the GNU General Public License
# generated by wxGlade 0.6 on Mon Mar 17 23:22:49 2008

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

Model
=====

The model contains the core data structures of pyspread.
It is divided into layers.

Layer 3: 
Layer 2: 
Layer 1: 
Layer 0: 

"""

from types import SliceType

from lib.irange import slice_range
from lib.selection import Selection

class CodeArray(DataArray):
    """CodeArray provides objects when accessing cells via __getitem__
    
    Cell code can be accessed via get_code
    
    This class represents layer 3 of the model.
    
    """
    
    get_code = DataArray.__getitem__
    
    def __getitem__(self, key):
        pass
    
# End of class CodeArray

# ------------------------------------------------------------------------------

class DataArray(object):
    """DataArray provides enhanced grid read/write access.
    
    Enhancements comprise:
     * Slicing
     * Multi-dimensional operations such as insertion and deletion of sub-arrays
     * Undo/redo operations
    
    This class represents layer 2 of the model.
    
    Parameters
    ----------
    shape: n-tuple of integer
    \tShape of the grid
    
    """
    
    def __init__(self, shape):
        self.dict_grid = DictGrid(shape)
    
    # Shape mask
    
    def _get_shape(self):
        return self.dict_grid.shape
        
    def _set_shape(self, shape):
        self.dict_grid.shape = shape
    
    shape = property(_get_shape, _set_shape)
        
    # Pickle support
    
    def __getstate__(self):
        """Returns dict_grid for pickling
        
        Note that all persistent data is contained in the DictGrid class
        
        """
        
        return {"dict_grid": self.dict_grid}
    
    # Slice support
    
    def __getitem__(self, key):
        """Adds slicing access to cell code retrieval
        
        The cells are returned as a generator of generators, of ... of unicode.
        
        Parameters
        ----------
        key: n-tuple of integer or slice
        \tKeys of the cell code that is returned
        
        Note
        ----
        Classical Excel type addressing (A$1, ...) may be added here
        
        """
        
        for key_ele in key:
            if hasattr(key_ele, "split"):
                # We have something string-like here 
                
                raise NotImplementedError
            
            elif hasattr(key_ele, "indices"):
                # We have something slice-like here 
                
                return self.cell_array_generator(key)
                
        # key_ele should be a single cell
        
        return self.dict_grid[key]
        
    def __setitem__(self, key, value):
        raise NotImplementedError
    
    def cell_array_generator(self, key):
        """Generator traversing cells specified in key
        
        Parameters
        ----------
        key: Iterable of Integer or slice
        \tThe key specifies the cell keys of the generator
        
        """
        
        for i, key_ele in enumerate(key):
            
            # Get first element of key that is a slice
            
            if type(key_ele) is SliceType:
                slc_keys = slicerange(key_ele, self.dict_grid.shape[i])
                
                key_list = list(key)
                
                key_list[i] = None
                
                has_subslice = any(type(ele) is SliceType for ele in key_list)
                                            
                for slc_key in slc_keys:
                    key_list[i] = slc_key
                    
                    if has_subslice:
                        # If there is a slice left yield generator
                        yield self.cell_array_generator(key_list)
                        
                    else:
                        # No slices? Yield value
                        yield self[tuple(key_list)]
                    
                break

# End of class DataArray


class UnRedo(object):
    """Undo/Redo framework class.
    
    For each undoable operation, the undo/redo framework stores the
    undo operation and the redo operation. For each step, a 4-tuple of:
    1) the function object that has to be called for the undo operation
    2) the undo function paarmeters as a list
    3) the function object that has to be called for the redo operation
    4) the redo function paarmeters as a list
    is stored.
    
    One undo step in the application can comprise of multiple operations.
    Undo steps are separated by the string "MARK".
    
    The attributes should only be written to by the class methods.

    Attributes
    ----------
    undolist: List
    \t
    redolist: List
    \t
    active: Boolean
    \tTrue while an undo or a redo step is executed.

    """
    
    def __init__(self):
        """[(undofunc, [undoparams, ...], redofunc, [redoparams, ...]), 
        ..., "MARK", ...]
        "MARK" separartes undo/redo steps
        
        """
        
        self.undolist = []
        self.redolist = []
        self.active = False
        
    def mark(self):
        """Inserts a mark in undolist and empties redolist"""
        
        if self.undolist != [] and self.undolist[-1] != "MARK":
            self.undolist.append("MARK")
    
    def undo(self):
        """Undos operations until next mark and stores them in the redolist"""
        
        self.active = True
        
        while self.undolist != [] and self.undolist[-1] == "MARK":
            self.undolist.pop()
            
        if self.redolist != [] and self.redolist[-1] != "MARK":
            self.redolist.append("MARK")
        
        while self.undolist != []:
            step = self.undolist.pop()
            if step == "MARK": 
                break
            self.redolist.append(step)
            step[0](*step[1])
        
        self.active = False
        
    def redo(self):
        """Redos operations until next mark and stores them in the undolist"""
        
        self.active = True
        
        while self.redolist and self.redolist[-1] == "MARK":
            self.redolist.pop()
        
        if self.undolist:
            self.undolist.append("MARK")
        
        while self.redolist:
            step = self.redolist.pop()
            if step == "MARK": 
                break
            self.undolist.append(step)
            step[2](*step[3])
            
        self.active = False

    def reset(self):
        """Empties both undolist and redolist"""
        
        self.__init__()

    def append(self, undo_operation, operation):
        """Stores an operation and its undo operation in the undolist
        
        undo_operation: (undo_function, [undo_function_attribute_1, ...])
        operation: (redo_function, [redo_function_attribute_1, ...])
        
        """
        
        # If the lists grow too large they are emptied
        if len(self.undolist) > MAX_UNREDO or \
           len(self.redolist) > MAX_UNREDO:
            self.reset()
        
        # Check attribute types
        for unredo_operation in [undo_operation, operation]:
            iter(unredo_operation)
            assert len(unredo_operation) == 2
            assert hasattr(unredo_operation[0], "__call__")
            iter(unredo_operation[1])
        
        if not self.active:
            self.undolist.append(undo_operation + operation)

# End of class UnRedo

# ------------------------------------------------------------------------------

class DictGrid(KeyValueStore):
    """The core data class with all information that is stored in a pys file.
    
    Besides grid code access via standard dict operations, it provides 
    the following attributes:
    
    * cell_attributes: Stores cell formatting attributes
    * macros:          String of all macros
    
    This class represents layer 1 of the model.
    
    Parameters
    ----------
    shape: n-tuple of integer
    \tShape of the grid
    
    """
    
    def __init__(self, shape):
        KeyValueStore.__init__(self)
        
        self.shape = shape
        
        self.cell_attributes = CellAttributes()
        self.macros = u""

# End of class DictGrid


class CellAttributes(list):
    """Stores cell formatting attributes in a list of 2 - tuples
    
    The first element of each tuple is a Selection.
    The second element is a dict of attributes that are altered.
    
    The class provides attribute read access to single cells via __getitem__
    Otherwise it behaves similar to a list.
    
    """
    
    def __getitem__(self, key, value):
        """Returns attribute dict for a single key"""
        
        assert not any(type(key_ele) is SliceType for key_ele in key)
        
        result_dict = {}
        
        for selection, attr_dict in self:
            if key in selection:
                result_dict.update(attr_dict)
        
        return result_dict

# End of class CellAttributes


# ------------------------------------------------------------------------------
class KeyValueStore(dict):
    """Key-Value store in memory. Currently a dict with default value None.
    
    This class represents layer 0 of the model.
    
    """
    
    def __missing__(self, value):
        """Returns the default value None"""
        
        return
        
# End of class KeyValueStore