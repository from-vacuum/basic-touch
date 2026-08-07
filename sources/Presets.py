"""
BasicTouch extension - Preset management module.
Handles presets

Presets are provided by an external callbacks DAT (referenced by the
`Presets Callbacks` parameter) that implements:

    def readPresets() -> list[str]
    def recall_preset(name: str, fade_time: float) -> None

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""

class PresetManager:
    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config
        self.presets = op('../presets')
        self.presets.clear()
        self.callbacks_dat = None
        self.presets_callbacks = self.config.presets_callbacks
        # Fade time passed to the callbacks on recall, in seconds
        self.max_fade_time = 10.0
        self.fade_time = 1.0
        if self.presets_callbacks:
            self.callbacks_dat = op(self.presets_callbacks)
            self.presets = op('../presets')
            # Default grid settings
            self.preset_grid_cols = 2
            self.preset_grid_rows = 4
            self.max_allowed_presets = 10

    @property
    def callbacks(self):
        """Module of the referenced callbacks DAT, or None if unavailable."""
        if self.callbacks_dat is None:
            return None
        try:
            return self.callbacks_dat.module
        except Exception as e:
            self.debug(f"Could not load presets callbacks module: {e}")
            return None

    def loadPresets(self):
        if self.presets_callbacks:
            self.presets.clear()
            callbacks = self.callbacks
            if callbacks and hasattr(callbacks, 'readPresets'):
                # append each preset name returned by the callbacks DAT
                for entry in callbacks.readPresets():
                    self.presets.appendRow([entry])
            else:
                self.debug("Presets callbacks not found or does not implement readPresets().")


    def sendPresetsToOSC(self):
            self.loadPresets()

            if self.callbacks_dat:
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

                # Send fade time fader, normalized to the fader's 0..1 range
                self.parent.osc_manager.sendOSC(
                    '/fadeTimeFader1', [self.fade_time / self.max_fade_time])
                self.parent.osc_manager.sendOSC(
                    '/color_control', ['fadeTimeFader', 1, *self.config.color])
                self.debug(f"Fade time set to {self.fade_time}")
            return


    def setFadeTime(self, normalized):
        """Store fade time from the normalized (0..1) OSC fader value."""
        self.fade_time = float(normalized) * self.max_fade_time
        self.debug(f"Fade time set to {self.fade_time}")

    def recall_preset(self, index):
        callbacks = self.callbacks
        if callbacks and hasattr(callbacks, 'recall_preset'):
            # get preset name by id from presets DAT
            preset_name = self.presets[index-1, 0].val
            self.debug(f"Recalling preset {preset_name} ")
            callbacks.recall_preset(preset_name, self.fade_time)
        else:
            self.debug("Presets callbacks not found or does not implement recall_preset().")

    def debug(self, message):
        self.parent.debug(message)
