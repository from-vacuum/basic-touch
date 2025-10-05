# 🎛️ BasicTouch

🎹 Want to play your visuals like an instrument, rather than jerking one parameter at a time with a mouse?

🖐️ Want to explore your patches parameter space with a tactile, expressive control surface?

🚶‍♂️ Want to walk around the room and tweak any parameter from anywhere on the touch surface of your choice?

🧱 Tired of building and rebuilding custom UI layouts for every new TouchDesigner project?


✨ BasicTouch is a dynamic OSC controller for TouchDesigner and TouchOSC that auto-generates a custom layout for any COMP’s parameters, syncs values both ways in real time.
🎲 With curated randomization and optional connection to TauCeti preset system.
🔟 10 touchpoints can control up to 20 parameters at the same time.

## 🧰 What You Need
- 🧠 **TouchDesigner** 2023.1+ (tested on 2025.30960)
- 📱 **TouchOSC** desktop or mobile
- 🧩 TOX/Base Comp with parameters to control (sliders, toggles, RGB colors, XY pads, menus)

## ✨ Why It’s Awesome

- 🧭 **Auto layout**: positions controls on the TouchOSC document for you.
- 🔄 **Live round-trip**: every tweak in TouchDesigner pushes values, colors, and modes to the controller; any performance wiggles from TouchOSC land straight back into your parameters.
- 🎲 **Randomize it**: eight chaos buttons plus a random-amount fader for dialing in just enough entropy.
- 🚀 **Preset launcher**: mirrors external preset manager(Tau Ceti), lays out up to 10 preset buttons, and syncs fade time.
- 📡 **UDP/TCP agnostic**: flip one toggle to switch between traditional UDP fire-and-forget or reliable TCP for wireless connections.


## 🛠️ How to Install and setup:

1. 📦 Drag `BasicTouch.tox` into TouchDesigner
2. 🎯 Set `Target Base` by dragging your target Base COMP
3. 🌐 Set Ports and IPs
	1. 🖥️ `Local IP` is where TouchDesigner running
	2. 📱 `Device IP` is where TouchOSC running
4. 📲 Open TouchOSC `BasicTouch.Beta.tosc` template on control surface device.
	1. 🧭 Edit -> Connections, on OSC tab, make sure IPs and Ports are aligned with step 3. 
		1. 📤 `Send Port` = `OUT Port`
		2. 📥 `Receive Port` = `IN Port`
	2. 🔺 Switch to **Control Surface View** by pressing triangle icon 
	3. ⏳ "Waiting for connection...." appears
5. ⚙️ Press "Setup Controls" on the Config page to send controls info to TouchOSC
6. 🎶 Jam on dynamic bidirectional control surface UI

🔁 To control another Base COMP, just change `Target Base` and press "Setup Controls" again.

## 🚀 TauCeti Support
 * 🛰️ [TauCeti PresetSystem](https://github.com/PlusPlusOneGmbH/TD_TauCeti_Presetsystem) - "Highly customisable and setup agnostic system for presets management
* 🎯 Point to your TauCeti Preset Manager COMP in `Preset Manager` parameter, and BasicTouch will:
	* 🧾 Auto populate preset buttons with names from TauCeti Preset Manager
	* 🔁 Sync preset changes from TouchOSC to TauCeti Preset Manager and vice versa
	* ⏱️ Sync fade time parameter to TauCeti Preset Manager's fade time parameter
* 🔟 Up to 10 preset buttons supported
* 🕙 Fade time control with maximum set to 10s

## 🎲 Randomization
*  8 Randomize buttons to randomize different sets of parameters
	-  4 buttons to randomize all parameters by 1/5/30/100 %
	-  4 buttons to randomize given parameter types: Fader/Button/Menu/XY(Z) to the amount set by Random Amount fader on the right

*  Randomization respects parameter types and ranges, and will not change parameters that are disabled or have expressions

## ⚠️ Important:

- 🎯 Make sure to set correct range max and range min for parameters for correct scaling
- 🔒 Parameters that have expressions will be displayed in `read-only` mode - no ability to change value, slow fade in/out
- 📐 Template Resolution **needs** to be the same as TouchOSC's Document `Width` and `Height`; if you change one, update the other. TouchOSC does not allow you to change those dynamically.
- 🔁 When you switch `Target Base` or change any of its Parameter config/names, just "Setup Controls" again to update TouchOSC template.
- ♻️ If something breaks, restart BasicTouch by disabling/enabling cooking via `X`
	* 🪪 "Toggle Log" in TouchOSC to see incoming OSC messages and troubleshoot connection.
 * 📶 TouchDesigner only work with OSC via UDP out of the box. BasicTouch supports TCP via custom script that have bugs, this feature is experimental. Use UDP over the wire if you can.
 * 🪲 Flip `Debug Log` on the components "About" page if you face any issues, and check Textport for errors.

## ❓ FAQ

-  **I am getting "Too many parameters for this document size"?**
   -  Your target Base COMP has more parameters than BasicTouch can handle with current TouchOSC document size.
   -  You can either reduce the number of parameters in your target Base COMP, or increase the TouchOSC document size or decrease "Minimum control height" in BasicTouch "Appearance" page.
   -  If you have a bunch of Button/Pulse/XY parameters, consider grouping them together so they can share one row and save space. 


## 🚧 Limitations

### 🗺️ Layout
 Layout of the document is vertical with single column, we may add more layout options in the future.

### 📏 Control Limits
 TouchOSC cannot create new controls, so we reuse pre-made controls. This puts some limits on how many parameters BasicTouch can handle per document size.
Here are the current limits:
 
 * 🎚️ Fader: 16
 * 🔘 Button: 16
 * 🌈 Color: 3
 * 📋 Menu: 4
 * 🧭 XY: 4

 Supported Parameter Styles:

- 🎚️ `float`
- 🔢 `int`
- ⚡ `pulse`
- 🔁 `toggle`
- ⏱️ `momentary`
- 🌈 `rgb`
- 📋 `menu`
- 🧾 `strmenu`
- 🧭 `xy`
- 🧮 `xyz`
- 🧊 `xyzw`

🚫 Any parameters beyond these limits will be ignored.
