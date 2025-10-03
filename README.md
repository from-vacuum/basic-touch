# BasicTouch

Want to play your visuals like an instrument, rather than jerking one parameter at a time with a mouse?
Want to explore your patches parameter space with a tactile, expressive control surface?
Want to walk around the room and tweak your visuals from anywhere on the touch surface of your choice?
Tired of building and rebuilding custom UI layouts for every new TouchDesigner project?


BasicTouch is a dynamic OSC controller for TouchDesigner and TouchOSC that auto-generates a custom layout for any COMP’s parameters, syncs values both ways in real time. 
With curated randomization and optional connection to TauCeti preset system.
10 touchpoints can control up to 20 parameters at the same time.

## What You Need
- **TouchDesigner** 2023.1+ (tested on 2025.30960)
- **TouchOSC** desktop or mobile
- TOX/Base Comp with parameters to control (sliders, toggles, RGB colors, XY pads, menus)

## Why It’s Awesome

- **Auto layout**: scans any COMP’s parameters, classifies them (faders, buttons, XY pads, RGB grouped triples) and positions controls on the TouchOSC document for you.
- **Live round-trip**: every tweak in TouchDesigner pushes values, colors, and modes to the controller; any performance wiggles from TouchOSC land straight back into your parameters.
- **Randomize rig**: eight curated chaos buttons plus a random-amount fader for dialing in just enough entropy.
- **Preset launcher**: mirrors external preset manager(Tau Ceti), lays out up to 10 preset buttons, and syncs fade time.
- **UDP/TCP agnostic**: flip one toggle to switch between traditional UDP fire-and-forget or reliable TCP for wireless connections.

## Quickstart in 5 Steps
1. **Drop the component**: place `/BasicTouch` inside your TouchDesigner project and point the `Base` parameter at the COMP whose parameters you want to control.
2. **Check network**: in the `Network` page, confirm IP/ports. Local testing defaults to `127.0.0.1`, `7000` out, `7003` in.
3. **Deploy TouchOSC**: open the bundled `BasicTouch.tosc` layout and point it back at TouchDesigner with matching ports.
4. **Pulse Setup Controls** in TD: fires the OSC boot sequence—layouts, colors, preset grid, randomize buttons, everything.
5. **Jam**: move anything—faders, toggles, XY, menus—on either side and watch the other side mirror it.


How to Install and setup:

1. Drag `BasicTouch` into TouchDesigner
2. Set `Target Base` by dragging your target Base COMP
3. Set Ports and IPs
	1. `Local IP` is where TouchDesigner running
	2. `Device IP` is where TouchOSC running
4. Open TouchOSC `BasicTouch.Beta.tosc` template on control surface device.
	1. Edit -> Connections, on OSC tab, make sure IPs and Ports are aligned with step 3. 
		1. `Send Port` = `OUT Port`
		2. `Recieve Port` = `IN Port`
	2. Switch to **Control Surface View** by pressing triangle icon 
	3. "Waiting for connection...." appears
5. Press "Setup Controls" on the Config page to send controls info to TouchOSC
6. Enjoy dynamic bidirectional Control Surface UI



## Tau Ceti Support
* max_allowed_presets = 10
* Fade time max is 10s

## Important:

* Make sure to set correct range max and range min for parameters for correct scaling
* Parameters that have expressions will be displayed in `read-only` mode - no ability to change value, slow fade in/out
* Template Resolution **need** to be the same as TouchOSCs Document `Width` and `Height` in case you changed one, update the other.  TouchOSC does not allow to change those dynamically.
* When you switch `Target Base` or change any of its Parameter config/names, just "Setup Controls" again to update TouchOSC template.
* If something breaks, restart BasicTouch by disabling/enabling cooking via `X`
	* "Toggle Log" in TouchOSC to see incoming OSC messages and troubleshoot connection.
 * TouchDesigner only work with OSC via UDP out of the box. BasicTouch supports TCP via custom script that have bugs, this feature is experimental. Use UDP over the wire if you can.
 *  Flip `Debug Log` on the components "About" page if you face any issues, and check Textport for errors.


## Limitations

 'label': 24,

            'fader': 16,

            'button': 16,

            'color': 3,

            'radio': 4,

            'xy': 4,

            'plabel': 10,

            'pbutton': 10

supported_styles = ['float', 'int', 'pulse', 'toggle', 'momentary', 'rgb', 'menu', 'strmenu', 'xy', 'xyz', 'xyzw']

- Layout is vertical with single column
- 


