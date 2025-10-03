"""
BasicTouch extension - Main class that orchestrates all modules.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0 
"""


class BasicTouch:
    def __init__(self, comp):
        self.comp = comp
        self.debug('Init BasicTouch...') 
        self.base_comp: Par = op(comp.par.Base)
        
        # Core components
        self.params_dat = op('param_control')
  
        # UI properties
        self.doc_width = comp.par.Templateresolutionw
        self.doc_height = comp.par.Templateresolutionh
        self.tab_bar_height = 50
        self.scale_height = comp.par.Scalecontrolsheight.eval()
        self.font_size = comp.par.Fontsize.eval()
        self.padding = 10
        self.min_control_height = comp.par.Mincontrolheight.eval()
        self.sleep_time = 0.01 # 10ms Sleep time for OSC messages
        
        # Should be in sync with TouchOSC file
        self.control_limits = {
            'label': 24,
            'fader': 16,
            'button': 16,
            'color': 3,
            'radio': 4,
            'xy': 4,
            'plabel': 10,
            'pbutton': 10
        }
        
        self.supported_styles = ['float', 'int', 'pulse', 'toggle', 'momentary', 'rgb', 'rgba', 'menu', 'strmenu', 'xy', 'xyz', 'xyzw']
        
        # Colors
        color_par = comp.par.Colorr
        self.color = [
            color_par.parGroup[0].eval(),
            color_par.parGroup[1].eval(),
            color_par.parGroup[2].eval()
        ]

        # Load modules 
        self.layout_manager = op('modules/Layout').module.Layout(self)
        self.osc_manager = op('modules/OSC').module.OSCManager(self)
        self.parameter_manager = op('modules/Parameters').module.ParameterManager(self)
        
        if comp.par.Presetmanager:
            self.preset_manager = op('modules/Presets').module.PresetManager(self)
        else:
            self.preset_manager = None
            op('presets').clear()
            
        self.randomize_manager = op('modules/Randomize').module.RandomizeManager(self)
        
    def Start(self):
        self.parameter_manager.loadParameters()
        # Calculate UI layout
        self.layout_manager.__init__(self)
        self.layout_manager.calculateControlInfo()
        self.layout_manager.calculateControlPositions()
        
        # Send controls to OSC
        self.osc_manager.resetOSC()
        self.osc_manager.sendControlsToOSC()
        
        # Set up randomization controls
        self.randomize_manager.sendRandomizeButtonsToOSC()
        
        # Set up presets if we have them
        if self.preset_manager:
            self.preset_manager.sendPresetsToOSC()
            
        # Send font size
        self.osc_manager.sendOSC('/tabs', [self.font_size, self.min_control_height])
    
    # Main extension callbacks - these delegate to the appropriate module
    def OnReceiveOSC_UDP(self, dat, rowIndex, message, byteData, timeStamp, address, args, peer):
        return self.osc_manager.OnReceiveOSC(dat, rowIndex, message, byteData, timeStamp, address, args, peer)
    
    def OnReceiveOSC_TCP(self, byteData):   
        return self.osc_manager.OnReceiveOSC_TCP(byteData)
        
    def OnValueChange(self, par, prev):
        return self.parameter_manager.OnValueChange(par, prev)
    
    def OnModeChange(self, par, prev):
        return self.parameter_manager.OnModeChange(par, prev)

    def OnEnableChange(self, par, val, prev):
        return self.parameter_manager.OnEnableChange(par, val, prev)    

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

    def debug(self, message):
        if self.comp and self.comp.par.Debuglog:
            debug(message)

    def showWarningDialog(self, message, title="Warning"):
        result = ui.messageBox(title, message) 
        return result
    