"""
BasicTouch extension - Randomization module.
Handles parameter randomization functionality.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""
import random

class RandomizeManager:
    def __init__(self, parent):
        self.parent = parent
        self.random_amount = 0.5
        
        # Set up randomization options
        self.random_buttons = {
            '1%': lambda: self.Randomize(degree=0.01, type='all'),
            '5%': lambda: self.Randomize(degree=0.05, type='all'),
            '30%': lambda: self.Randomize(degree=0.3, type='all'),
            '100%': lambda: self.Randomize(degree=1.0, type='all'),
            'Fader': lambda: self.Randomize(degree=self.random_amount, type='fader'),
            'Button': lambda: self.Randomize(degree=self.random_amount, type='button'),
            'Menu': lambda: self.Randomize(degree=self.random_amount, type='radio'),
            'XY(Z)': lambda: self.Randomize(degree=self.random_amount, type='xy')
        }
        
    def Randomize(self, degree=0.5, type='all'):
        """
        Randomize controls
        
        Args:
            degree (float): Amount of randomization from 0.0 to 1.0
                where 0.0 means no change and 1.0 means full randomization
            type (str): Type of controls to randomize. Can be 'all', 'fader', 
                'button', 'color', 'radio', 'xy'
        """
        self.parent.debug(f"Randomizing controls of type '{type}' with degree {degree}...")
        
        for row in range(1, self.parent.params_dat.numRows):
            param_name = self.parent.params_dat[row, 'name'].val
            control_type = self.parent.params_dat[row, 'control_type'].val
            
            # Skip if not matching the requested type
            if type != 'all' and (control_type != type):
                continue
                
            par = self.parent.base_comp.par[param_name]
            if par is None:
                continue
            
            # Skip parameters that are not in constant mode
            if par.mode != ParMode.CONSTANT:
                continue
                
            if par.isNumber:
                # Scale randomization around current value
                current = par.normVal
                random_val = random.random()
                # Blend between current value and random value based on degree
                new_val = current + (random_val - current) * degree
                # Ensure value stays within bounds
                par.normVal = max(0.0, min(1.0, new_val))
            elif par.isPulse:
                # Only pulse with probability based on degree
                if random.random() < degree:
                    par.pulse()
            elif par.isToggle:
                # Only toggle with probability based on degree
                if random.random() < degree:
                    par.val = random.choice([True, False])
            elif par.isMenu:
                # Only change menu with probability based on degree
                if random.random() < degree:
                    par.menuIndex = random.randint(0, len(par.menuLabels)-1)
        return

    def randomize(self, index):
        """
        Trigger a specific randomization function by index
        
        Args:
            index (int): Index of the randomization button pressed
        """
        # Get the corresponding randomization function from the dictionary
        random_func = self.random_buttons.get(
            list(self.random_buttons.keys())[index-1])
        if random_func:
            random_func()
    
    def sendRandomizeButtonsToOSC(self):
        """
        Create and send OSC messages for randomization buttons
        """
        cols = 2
        rows = 4
        button_width = self.parent.doc_width - (self.parent.padding * 2)
        button_height = (self.parent.doc_height - (self.parent.padding * 2))
        
        available_width = self.parent.doc_width - (self.parent.padding * (cols+1)) - 80  # amount fader
        available_height = self.parent.doc_height - (self.parent.padding * (rows+1)) - 40  # bar
            
        button_width = available_width / cols
        button_height = available_height / rows
            
        positions = self.parent.layout_manager.calculateGridPositions(
            cols*rows, cols, rows, 
            button_width, button_height, 
            self.parent.padding
        )

        # iterate through buttons and send OSC messages
        for i, button in enumerate(self.random_buttons.keys()):
            if i < len(positions):
                x, y, width, height = positions[i]
                self.parent.osc_manager.sendOSC('/add_random', [
                    i+1, button, x, y, width, height, *self.parent.color
                ])
                self.parent.debug(f"Added random button {button} to OSC at position ({x}, {y})")
        
        # Add randomization amount slider
        self.parent.osc_manager.sendOSC('/modify_control', [
            'RandomAmount', 1, 
            self.parent.doc_width-70, 0, 
            50, self.parent.doc_height-80, 
            'constant'
        ])
        self.parent.osc_manager.sendOSC('/Randomize/RandomAmount1', [self.random_amount])
        self.parent.osc_manager.sendOSC('/color_control', ['RandomAmount', 1, *self.parent.color])