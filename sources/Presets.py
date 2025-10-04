"""
BasicTouch extension - Preset management module.
Handles presets 

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""

class PresetManager:
    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config
        self.presets = op('../presets')
        self.presets.clear()
        self.tauceti_manager = None
        self.preset_manager_path = self.config.preset_manager_path
        if self.preset_manager_path:
            self.tauceti_manager = op(self.preset_manager_path)
            self.presets = op('../presets')
            # Default grid settings
            self.preset_grid_cols = 2
            self.preset_grid_rows = 4
            self.max_allowed_presets = 10

    def loadPresets(self):
        if self.preset_manager_path:
            self.presets.clear()
            if self.tauceti_manager and hasattr(self.tauceti_manager, 'PresetParMenuObject'):
                # append each entry from MenuSource to the presets DAT
                for entry in self.tauceti_manager.PresetParMenuObject.menuNames:
                    self.presets.appendRow([entry])
            else:
                self.debug("Preset manager not found or does not have the required attribute.")


    def sendPresetsToOSC(self):
            self.loadPresets()
            
            if hasattr(self, 'tauceti_manager'):
                # Calculate preset button dimensions
                num_presets = self.presets.numRows
                if num_presets == 0:
                    self.debug("No presets found")
                    return

                # Check if we have more than the maximum allowed presets

                if num_presets > self.max_allowed_presets:
                    self.parent.showWarningDialog(
                        f"You have {num_presets} presets, but only {self.max_allowed_presets} can be displayed. "
                        f"Some presets will not be accessible through the interface.",
                        "Too Many Presets"
                    )
                    num_presets = self.max_allowed_presets

                # Define grid layout properties
                cols = self.preset_grid_cols
                rows = self.preset_grid_rows

                # Calculate maximum items that can fit in the grid
                max_items = cols * rows

                # Adjust grid if we have fewer presets than grid cells
                if num_presets < max_items:
                    # Calculate optimal columns and rows for fewer items
                    if num_presets <= cols:
                        actual_cols = num_presets
                        actual_rows = 1
                    else:
                        actual_cols = cols
                        # Ceiling division
                        actual_rows = (num_presets + cols - 1) // cols
                else:
                    actual_cols = cols
                    actual_rows = (num_presets + cols - 1) // cols

                # Calculate item size based on available space
                available_width = self.config.doc_width - \
                    (self.config.padding * (actual_cols + 1))
                available_height = self.config.doc_height - \
                    (self.config.padding * (actual_rows + 1)) - \
                    120  # bar and fade time fader

                button_width = available_width / actual_cols
                button_height = available_height / actual_rows

                # Calculate positions for all preset buttons
                positions = self.parent.layout_manager.calculateGridPositions(
                    num_presets, actual_cols, actual_rows,
                    button_width, button_height,
                    self.config.padding
                )

                # Send OSC messages for each preset
                for row in range(0, self.presets.numRows):
                    if row < len(positions):
                        x, y, width, height = positions[row]
                        preset_name = self.presets[row, 0].val

                        self.parent.osc_manager.sendOSC('/add_preset', [
                            row+1, preset_name, x, y, width, height, *self.config.color
                        ])

                        self.debug(
                            f"Added preset {preset_name} to OSC at position ({x}, {y})")

                # Send fade time fader from Interacttime parameter of Tauceti manager
                if self.tauceti_manager.par.Interacttime:
                    fade_time = self.tauceti_manager.par.Interacttime.eval()
                    self.parent.osc_manager.sendOSC('/fadeTimeFader1', [fade_time])
                    self.parent.osc_manager.sendOSC(
                        '/color_control', ['fadeTimeFader', 1, *self.config.color])
                    self.debug(f"Fade time set to {fade_time}")
            return


    def recall_preset(self, index):
        if hasattr(self, 'tauceti_manager'):
            # get preset name by id from presets DAT
            preset_name = self.presets[index-1, 0].val
            self.debug(f"Recalling preset {preset_name} ")
            self.tauceti_manager.Recall_Preset(
                preset_name, self.tauceti_manager.par.Interacttime.eval())

    def debug(self, message):
        self.parent.debug(message)
