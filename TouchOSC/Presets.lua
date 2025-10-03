function onReceiveOSC(message, connections)
    local path = message[1] -- OSC address
    local arguments = message[2]
    
    -- Handle add_preset messages
    if path == "/add_preset" then
        if #arguments >= 6 then
            local index = tonumber(arguments[1].value)
            local name = arguments[2].value
            local x = tonumber(arguments[3].value) or 0
            local y = tonumber(arguments[4].value) or 0
            local width = tonumber(arguments[5].value) or 100
            local height = tonumber(arguments[6].value) or 100
            
            -- Get color values if provided (optional)
            local r = tonumber(arguments[7] and arguments[7].value) or 1
            local g = tonumber(arguments[8] and arguments[8].value) or 1
            local b = tonumber(arguments[9] and arguments[9].value) or 1
            
            local buttonName = "pbutton" .. index
            local labelName = "plabel" .. index
            
            local button = self:findByName(buttonName, true)
            local label = self:findByName(labelName, true)
            
            if button and label then
                -- Set positions and dimensions
                button.frame.x = x
                button.frame.y = y
                button.frame.w = width
                button.frame.h = height
                
                -- Set label to same position as button
                label.frame.x = x
                label.frame.y = y + (height * 0.1)
                label.frame.w = width
                label.frame.h = height * 0.8
                
                -- Set the label's value to the provided name
                label.values['text'] = name
                
                -- Set colors for both button and label
                button.color.r = r
                button.color.g = g
                button.color.b = b
                
                label.color.r = r
                label.color.g = g
                label.color.b = b
                
                -- Set visibility
                button.visible = true
                label.visible = true
                self.parent.parent.tabbar = true
                
                -- Make parent visible if needed
                if button.parent then
                    button.parent.visible = true
                end
                
                print(string.format("Added preset %s at (%d,%d) size %dx%d with color RGB(%.2f,%.2f,%.2f)", 
                    name, x, y, width, height, r, g, b))
            else
                print(string.format("Could not find button%s or label%s for preset!", index, index))
            end
        else
            print("Error: Missing arguments for /add_preset")
        end
       
    end
end

function init()
 self.frame.h = root.frame.h
 self.frame.w = root.frame.w
end