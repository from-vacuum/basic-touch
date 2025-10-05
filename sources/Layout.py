"""
BasicTouch extension - Layout management module.
Handles all control positioning and layout calculations.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""

class Layout:
    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config
        self.dat = self.parent.params_dat
        
        for col in ['control_type', 'control_index', 'address',
                    'x', 'y', 'width', 'height']:
            if col not in self.dat.cols():
                self.dat.appendCol(col)

    def calculateControlInfo(self):
        # Split responsibilities via helpers; explicit grouping state; reduced duplication
        control_indices = {'fader': 0, 'button': 0, 'color': 0, 'radio': 0, 'xy': 0}
        group_state = {'xy_count': 0, 'color_count': 0}
        
        for row in range(1,  self.dat.numRows):
            style_cell = self.dat[row, "style"]
            if not style_cell:
                continue
            
            control_type = self._classify_control_type(row, style_cell.val.lower(), self.dat[row, "size"])
            if not control_type:
                continue
            
            index = self._next_index(control_type, group_state, control_indices)
            if index > self.config.control_limits.get(control_type, 0):
                self.parent.showWarningDialog(f"Ran out of control for type [{control_type}]")
                self.removeParamRows(row)
                continue

            self._write_row(row, control_type, index)
        return

    def _classify_control_type(self, row: int, style: str, size: str = "") -> str:
        if style in ('float', 'int', 'xy', 'xyzw'):
            if size == "1":
                return 'fader'
            if size == "2":
                return 'xy'
            if size == "3":
                prev_label = self.dat[row-2, 'label'].val if row > 2 else None
                label = self.dat[row, 'label'].val
                if prev_label == label:
                    return 'fader'
                return 'xy'
            return ''
        if style in ('pulse', 'toggle', 'momentary'):
            return 'button'
        if style in ('rgb', 'rgba'):
            return 'color'
        if style in ('menu', 'strmenu'):
            return 'radio'
        # if style in ('xy', 'xyzw'):
        #     # # Special-case: when two rows above is 'xyzw', treat current as fader
        #     # prev2 = self.dat[row-2, 'style'] if row > 2 else None
        #     # if prev2 and prev2.val.lower() == 'xyzw' and size == "3":
        #     #     return 'fader'
        #     return 'xy'
        return ''

    def _next_index(self, control_type: str, group_state: dict, control_indices: dict) -> int:
        """Update grouping counters and return the control index to use for this row."""
        if control_type == 'xy':
            group_state['xy_count'] += 1
            # Increment index on the first of every XY pair
            if (group_state['xy_count'] - 1) % 2 == 0:
                control_indices['xy'] += 1
            return control_indices['xy']
        elif control_type == 'color':
            group_state['color_count'] += 1
            # Increment index on the first of every RGB triplet
            if (group_state['color_count'] - 1) % 3 == 0:
                control_indices['color'] += 1
            return control_indices['color']
        else:
            control_indices[control_type] += 1
            return control_indices[control_type]

    def _write_row(self, row: int, control_type: str, index: int) -> None:
        """Write computed info back to the DAT for the given row."""
        self.parent.debug(f"Control type: {row} {[c.val for c in self.dat.row(row)]}")
        self.dat[row, "control_type"] = control_type
        self.dat[row, 'control_index'] = str(index)
        address = f"/{control_type}{index}"
        self.dat[row, 'address'] = address
        
        par_name_cell = self.dat[row, 'name']
        if par_name_cell:
            par = self.parent.base_comp.par[par_name_cell.val]
            if par is not None:
                self.dat[row, 'mode'] = self.parent.parameter_manager.param_mode(par)
        return

    def calculateControlPositions(self):
        """Calculate positions for all controls based on their types"""
        y = self.config.padding
        
        row = 1
        while row < self.dat.numRows:
            control_type = self.dat[row, 'control_type'].val
            if control_type == '':
                row += 1
                continue
            
            x = self.config.padding

            # Handle different control types with dedicated functions
            if control_type == 'button':
                # Check for consecutive buttons and position them
                row, y = self.position_buttons(row, y)
            elif control_type == 'xy':
                # Position XY controls (possibly in pairs)
                row, x, y = self.position_xy_control(row, x, y)
            elif control_type == 'color':
                # Position color controls (rgb/rgba triplets) and skip their extra rows
                row, y = self.position_color_control(row, x, y)
            else:
                # Position standard controls (fader, radio, etc.)
                row, y = self.position_standard_control(row, x, y)

            # Check if we're running out of vertical space
            if y > self.config.doc_height - self.config.tab_bar_height:
                self.parent.showWarningDialog(
                    f"Too many parameters for this document size.\nThe rest will be skipped.",
                    f"Too many parameters: {row}:{self.dat.numRows} {y} {self.control_height()}"
                )
                self.removeParamRows(row)
                break
        
        return

    def position_buttons(self, row, y):
        """Position buttons, grouping consecutive ones horizontally"""
        # Count consecutive buttons (up to 5)
        button_count = 1
        button_rows = [row]
        
        for check_row in range(row + 1, min(row + 5, self.dat.numRows)):
            if self.dat[check_row, 'control_type'].val == 'button':
                button_count += 1
                button_rows.append(check_row)
            else:
                break
        
        # Calculate width for each button
        available_width = self.config.doc_width - (self.config.padding * (button_count + 1))
        button_width = available_width / button_count
        button_height = self.control_height()
        
        # Position each button
        for i, btn_row in enumerate(button_rows):
            btn_x = self.config.padding + i * (button_width + self.config.padding)

            self.dat[btn_row, 'x'] = btn_x
            self.dat[btn_row, 'y'] = y
            self.dat[btn_row, 'width'] = button_width
            self.dat[btn_row, 'height'] = button_height

        # Move to next row and return updated position
        next_row = button_rows[-1] + 1
        next_y = y + button_height + self.config.padding
        return next_row, next_y

    def position_xy_control(self, row, x, y):
        """Position XY control and handle its components"""
        control_height = self.config.doc_width/2 - self.config.padding*2
        control_width = control_height
        
        # If previous control is also XY, join into one row
        if row > 2 and self.dat[row-1, 'control_type'].val == 'xy':
            x = float(self.dat[row-1, 'x'].val) + control_width + self.config.padding
            y = float(self.dat[row-1, 'y'].val)
        
        self.dat[row, 'x'] = x
        self.dat[row, 'y'] = y
        self.dat[row, 'width'] = control_width
        self.dat[row, 'height'] = control_height
        
        # Check if the next row is the Y component of this XY control
        control_index = self.dat[row, 'control_index'].val
        next_row = row + 1

        if (row < self.dat.numRows - 1 and 
            self.dat[row+1, 'control_type'].val == 'xy' and
            self.dat[row+1, 'control_index'].val == control_index):
            
            self.dat[row+1, 'x'] = x
            self.dat[row+1, 'y'] = y
            self.dat[row+1, 'width'] = control_width
            self.dat[row+1, 'height'] = control_height
            
            next_row = row + 2  # Skip to after the Y component
        else:
            next_row = row + 1
        
        next_y = y + control_height + self.config.padding
        return next_row, x, next_y

    def position_color_control(self, row, x, y):
        """Position a color control composed of 3 rows (rgb/rgba) sharing one index.
        If the next rows belong to the same color group, give them the same rect and skip them.
        """
        control_width = self.control_width()
        control_height = self.control_height()
        
        # Base position for the color control (apply to up to 3 rows)
        self.dat[row, 'x'] = x
        self.dat[row, 'y'] = y
        self.dat[row, 'width'] = control_width
        self.dat[row, 'height'] = control_height
        
        idx = self.dat[row, 'control_index'].val
        next_row = row + 1
        
        # If the next rows are color with same index, align them to the same rect and skip
        if next_row < self.dat.numRows and self.dat[next_row, 'control_type'].val == 'color' and self.dat[next_row, 'control_index'].val == idx:
            self.dat[next_row, 'x'] = x
            self.dat[next_row, 'y'] = y
            self.dat[next_row, 'width'] = control_width
            self.dat[next_row, 'height'] = control_height
            
            third_row = next_row + 1
            if third_row < self.dat.numRows and self.dat[third_row, 'control_type'].val == 'color' and self.dat[third_row, 'control_index'].val == idx:
                self.dat[third_row, 'x'] = x
                self.dat[third_row, 'y'] = y
                self.dat[third_row, 'width'] = control_width
                self.dat[third_row, 'height'] = control_height
                next_row = row + 3
            else:
                next_row = row + 2
        
        next_y = y + control_height + self.config.padding
        return next_row, next_y

    def position_standard_control(self, row, x, y):
        """Position standard controls like faders, radio buttons, etc."""
        self.dat[row, 'x'] = x
        self.dat[row, 'y'] = y
        self.dat[row, 'width'] = self.control_width()
        self.dat[row, 'height'] = self.control_height()
        
        next_row = row + 1
        next_y = y + self.control_height() + self.config.padding
        return next_row, next_y
    
    def removeParamRows(self, start_row):
        for row in range(start_row, self.dat.numRows):
            self.dat.deleteRow(start_row)
        return

        
    def calculateGridPositions(self, total_items, cols, rows, item_width, item_height, padding):
        positions = []
        
        for i in range(total_items):
            # Calculate row and column for this item
            col = i % cols
            row = i // cols
            
            # Calculate x and y positions
            x = padding + col * (item_width + padding)
            y = padding + row * (item_height + padding)
            
            positions.append((x, y, item_width, item_height))
            
        return positions
    
    def control_height(self):
        if not getattr(self.config, 'scale_controls_height', 0):
            return self.config.min_control_height
        else:
            # Calculate scaled height with minimum of self.min_control_height
            num_controls = sum(1 for row in range(1, self.dat.numRows)
                             if self.dat[row, 'control_type'].val)
            if not num_controls:
                return self.config.min_control_height

            scaled_height = (self.config.doc_height - (self.config.padding * (num_controls + 1))) // num_controls
            return max(self.config.min_control_height, scaled_height)

    def control_width(self):
        return self.config.doc_width - (self.config.padding * 2)
