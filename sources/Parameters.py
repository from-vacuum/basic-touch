"""
BasicTouch extension - Parameter management module.
Handles parameter value changes and updates.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""

class ParameterManager:
    def __init__(self, parent):
        self.parent = parent
        self.param_mappings = self.map_address() # name -> (index, address)
        self.params_dat = self.parent.params_dat
        self.osc_manager = self.parent.osc_manager
        self._parameter_locked = False
        
    def loadParameters(self):
        self.params_dat.clear()
        self.params_dat.copy(op('../source_parameters'))
        self.delete_unsupported()
        self.parent.debug("Parameters loaded and unsupported styles deleted")
        
    def delete_unsupported(self):
        rows_to_delete = []
        for row in range(1, self.params_dat.numRows):
            if not self.params_dat[row, 'style'] or self.params_dat[row, 'style'].val.lower() not in self.parent.supported_styles:
                rows_to_delete.append(row)
                self.parent.debug(f"Skipping parameter {self.params_dat[row, 'name'].val} with unsupported style")
        
        for row in sorted(rows_to_delete, reverse=True):
            self.params_dat.deleteRow(row)
        
    def map_address(self) -> dict:
        param_mappings = {}
        for row in range(1, self.parent.params_dat.numRows):
            name = self.parent.params_dat[row, 'name'].val
            param_mappings[name] = (row, self.parent.params_dat[row, 'address'].val)
        return param_mappings
        

        
    def OnValueChange(self, par, prev):
        """Handle parameter value changes and send OSC messages"""
        
        if self._parameter_locked:
            return

        if par.name in self.param_mappings:
            row, address = self.param_mappings[par.name]
   
            if par.mode == ParMode.EXPRESSION:
                return  # TODO: Implement expressions handling
   
            value = self.calculate_parameter_value(par)
            
            self.osc_manager.sendOSC(address, value)
            self.parent.debug(f"Parameter {par.name} [{address}] changed to {value}")
        else:
            self.parent.debug(f"Parameter {par.name} not found in mappings")
        
        return
    
    def param_mode(self, par) -> str:
        mode = str(par.mode).replace('ParMode.', '').lower()
        if par.readOnly or par.enable == False or mode == "expression":
            return 'readonly'
        return mode
        
    def OnModeChange(self, par: Par, prev: ParMode):
        if par.name in self.param_mappings:
            mode = self.param_mode(par)
            row, _ = self.param_mappings[par.name]
            self.parent.debug(f"Mode changed for {par.name}, mode: {mode}, previous: {prev}")
    
            if self.parent.params_dat[row, 'mode'].val != mode:
                    self.osc_manager.sendOSC('/mode_changed_control', [
                                        self.params_dat[row, 'control_type'].val,
                                        self.params_dat[row, 'control_index'].val,
                                        mode
                                    ])
                    self.params_dat[row, 'mode'] = mode    
        
    def calculate_parameter_value(self, par):
        """Calculate parameter value based on its type"""
        if len(par.parGroup) > 1:
            if par.style == 'XYZ' and par.parGroup[2]==par:
                # Return Z part of XYZ
                return [par.parGroup[2].normVal]
            
            return [float(p.normVal) for p in par.parGroup]
        elif par.isNumber:
            return [par.normVal]
        elif par.isMenu:
            return [par.menuIndex]
        else:
            return [1 if par.eval() else 0]

    def update_parameter_value(self, param, args):
        """Update parameter value based on its type"""
        try:
            self._parameter_locked = True
            
            if len(param.parGroup) > 1:
                self.parent.debug(f"Updating parameter group {param.name} with {args}")
                if len(param.parGroup) == 3 and len(args) == 1:
                    # Update Z part of XYZ - single value
                    param.parGroup[2].normVal = float(args[0])
                else:	
                    for i, p in enumerate(param.parGroup):
                            if i < len(args):
                                p.normVal = float(args[i])
            else:
                value = float(args[0])
                if param.isNumber:
                    param.normVal = value
                elif param.isPulse:
                    param.pulse()
                elif param.isToggle:
                    param.val = bool(value)
                elif param.isMomentary:
                    param.val = bool(value)
                elif param.isMenu:
                    param.menuIndex = int(value)
                    
        finally:
            run("args[0]._release_lock()", self, delayFrames=4)

    def _release_lock(self):
        self._parameter_locked = False
