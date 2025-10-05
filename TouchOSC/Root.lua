function init()
  welcomeScreen(true)
end

function onReceiveOSC(message, connections)
    welcomeScreen(false)
    
    if not message[1]:match("_control$") then
        return  -- pass to routing table
    end
    
    local path = message[1] -- OSC address
    local arguments = message[2]

    local controlType = arguments[1].value
    
    local controlIndex = tonumber(arguments[2].value)
    
    if not controlType or not controlIndex then
    
      print('\t path        =', path)
      for i = 1, #arguments do
        print('\t argument    =', arguments[i].tag, arguments[i].value)
      end

      local controlType = arguments[1].value
      print("Control type after extraction:", controlType)

      local controlIndex = tonumber(arguments[2].value)
      print("Control index after extraction:", controlIndex)
      print("Error: Missing control type or index")
        
      return true
    end

    local controlName = string.format("%s%d", controlType, controlIndex)
    
    local control = self:findByName(controlName, true)
    
    if control then
        if path == "/modify_control" then

            local x = tonumber(arguments[3].value) or 0
            local y = tonumber(arguments[4].value) or 0
            local w = tonumber(arguments[5].value) or 100
            local h = tonumber(arguments[6].value) or 100
            local mode = arguments[7].value or "constant"
            
            control.frame.x = x
            control.frame.y = y
            control.frame.w = w
            control.frame.h = h
            control.visible = true
            print(string.format("Made visible %s control",controlName))
            -- make the group visible as well
            control.parent.visible = true
            
            
            if arguments[9] and arguments[9].value then
              -- options for menu(radio)
              print(string.format("Options for %s control",controlName))
              control.parent:notify(control.name, arguments)
            end
            
            control.parent:notify(mode, controlName)
              
            print(string.format("Updated %s at (%d,%d) size %dx%d, mode %s", 
            controlName, x, y, w, h, mode))
        end
        
        if path == "/mode_changed_control" then
          control.parent:notify(arguments[3].value, controlName)
        end
        
        if path == "/color_control" then
          updateColor(control, arguments[3].value, arguments[4].value,arguments[5].value)
        end

        if path == "/hide_control" then
           control.visible = false
        end
        
    else
        print(string.format("Control '%s' not found!", controlName))
    end
    
    return true

end



function updateColor(control, r,g,b)
  control.color.r = r
  control.color.g = g
  control.color.b = b
  local child = control:findByName(control.name)
  if child then
    updateColor(child,r,g,b)
  end
end

function welcomeScreen(visible)
  self.children.WelcomeScreen.visible = visible
  self.children.WelcomeScreen.children.bg.visible = visible
  self.children.WelcomeScreen.children.waiting.visible = visible
  local tabs = self:findByName("Tabs", true)
  tabs.visible = not visible
end