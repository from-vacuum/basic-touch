"""
BasicTouch extension - Main class that orchestrates all modules.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0 
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

class BasicTouch:
    def __init__(self, comp: COMP):
        self.config: BasicTouchConfig = BasicTouchConfig.from_comp(comp)
        self.debug('Init BasicTouch...')
        self.base_comp: Optional[OPShortcut] = op(self.config.base_comp_path) if self.config.base_comp_path else None

        self.params_dat: tableDAT = op('param_control')

        # Load modules 
        self.layout_manager = op('modules/Layout').module.Layout(self)
        self.osc_manager = op('modules/OSC').module.OSCManager(self)
        self.parameter_manager = op('modules/Parameters').module.ParameterManager(self)

        if self.config.preset_manager_path:
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
        self.osc_manager.sendOSC('/tabs', [self.config.font_size, self.config.min_control_height])
    
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
        return self.parameter_manager.OnModeChange(par, prev)    

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

    def debug(self, message):
        if self.config.debug_log:
            debug(message)

    def showWarningDialog(self, message, title="Warning"):
        result = ui.messageBox(title, message) 
        return result
    


@dataclass(frozen=True)
class BasicTouchConfig:
    base_comp_path: str
    doc_width: float
    doc_height: float
    tab_bar_height: float
    scale_controls_height: float
    font_size: float
    padding: float
    min_control_height: float
    sleep_time: float
    control_limits: Dict[str, int]
    supported_styles: List[str]
    color: Tuple[float, float, float]
    preset_manager_path: Optional[str]
    use_udp_tcp: bool
    debug_log: bool

    @classmethod
    def from_comp(cls, comp: COMP) -> "BasicTouchConfig":
        """Build a configuration snapshot from the component's parameters."""
        def fetch(name: str):
            return _eval_par_value(getattr(comp.par, name, None))

        preset_manager_raw = fetch("Presetmanager")
        preset_manager_path = (
            preset_manager_raw.strip()
            if isinstance(preset_manager_raw, str) and preset_manager_raw
            else None
        )

        return cls(
            base_comp_path=str(fetch("Base") or ""),
            doc_width=float(fetch("Templateresolutionw")),
            doc_height=float(fetch("Templateresolutionh")),
            scale_controls_height=float(fetch("Scalecontrolsheight")),
            font_size=float(fetch("Fontsize")),
            min_control_height=float(fetch("Mincontrolheight")),
            use_udp_tcp=bool(fetch("Udptcp")),
            debug_log=bool(fetch("Debuglog")),
            preset_manager_path=preset_manager_path,
            color=[
                comp.par.Colorr.parGroup[0].eval(),
                comp.par.Colorr.parGroup[1].eval(),
                comp.par.Colorr.parGroup[2].eval()
            ],
            tab_bar_height=50.0,
            padding=10.0,
            sleep_time=0.01,
            control_limits={
                "label": 24, "fader": 16, "button": 16, "color": 3,
                "radio": 4, "xy": 4, "plabel": 10, "pbutton": 10,
            },
            supported_styles=[
                "float", "int", "pulse", "toggle", "momentary",
                "rgb", "rgba", "menu", "strmenu", "xy", "xyz", "xyzw",
            ],
        )

def _eval_par_value(par: Optional[Par]) -> Union[float, int, str, bool, None]:
    """Safely evaluate a TouchDesigner parameter."""
    if par is None:
        return None

    # Many TD parameter types expose eval(); fall back to val when missing.
    if hasattr(par, "eval"):
        value = par.eval()
    else:
        value = getattr(par, "val", None)

    # When the parameter resolves to an OP, store its path for serialization.
    if hasattr(value, "path"):
        return value.path

    return value
