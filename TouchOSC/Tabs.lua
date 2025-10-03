function init()
 self.tabbar = true
 self.values['page'] = 0
 self.frame.h = root.frame.h
 self.frame.w = root.frame.w
-- self.children[1].visible= true
-- self.children[2].visible = true
--self.children[2].visible= true
--self.children[3].visible= true
end


function onReceiveOSC(message, connections)
    updateFontSize(message[2][1].value)
    print("Updating BarSize to", message[2][2].value)
    self.tabbarSize = message[2][2].value
end

function updateFontSize(size)
  print("Updating font size to", size)
  local labels = self:findAllByType(ControlType.LABEL, true)
    
  for i=1,#labels do
    labels[i].textSize = size
  end
  
  local tabs = root.children.Tabs
  tabs.textSizeOn = size
  tabs.textSizeOff = size
  
end