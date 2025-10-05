 function onReceiveNotify(controlName, arguments)
  
  if controlName == "constant" then return end
  if controlName == "readonly" then
    local name = arguments
    local control = self.children[name]
    control.interactive = false
    control.children[name].interactive = false
    return
  end
  
  local control = self.children[controlName]
  
  if not control then return end
  
  local radio = control.children[controlName]
  local options = #arguments-9
  radio.steps=options
  
  control.interactive = true
  radio.interactive = true
 
  local x = tonumber(arguments[3].value) or 0
  local y = tonumber(arguments[4].value) or 0
  local w = tonumber(arguments[5].value) or 100
  local h = tonumber(arguments[6].value) or 100
  
  radio.frame.x = 0
  radio.frame.y = 0
  radio.frame.w = w
  radio.frame.h = h
  radio.visible = true
  for i = 1, 20 do
     local radioLabelName = string.format("%s%s%s",control.name,"label",i)
     local radioLabel = control.children[radioLabelName]
      if i>options then
        radioLabel.visible = false
     else
                  radioLabel.values.text = arguments[8+i].value
                  radioLabel.frame.x = (i-1)*(w/options)
                  radioLabel.frame.y = 0
                  radioLabel.frame.w = w/options
                  radioLabel.frame.h = h
                  radioLabel.visible = true
      end
    end
 end
 
function update()
  local children = self:findAllByProperty('interactive', false, true)
  for i=1,#children do
      children[i].color.a =math.abs(math.sin(0.0012*getMillis()))
  end 
end

function init()
 self.frame.h = root.frame.h
 self.frame.w = root.frame.w
end