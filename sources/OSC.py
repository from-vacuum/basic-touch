"""
BasicTouch extension - OSC communication module.
Handles sending/receiving OSC messages.

Created by: @from.vacuum aka Serhiy P.

Licence: CC0
"""
import time
import struct
from typing import List


class OSCManager:
    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config
        self.UDP_TCP = self.config.use_udp_tcp

        self.tcp = op('../tcpip1')
        self.udp = op('../oscout2')
        self.osc_in = op('../oscin2')
        
    def sendOSC(self, address, args):
       if not self.UDP_TCP:
           self.parent.debug(f"sendOSC_UDP called: {address} {args}")
           self.sendOSC_UDP(address, args)
       else:
           self.parent.debug(f"sendOSC_TCP called: {address} {args}")
           self.sendOSC_TCP(address, args)        
    
    def sendOSC_UDP(self, address, args):
        self.udp.sendOSC(address, args)

    def sendOSC_TCP(self, address, args):
        """Build an OSC packet, SLIP-encode it (OSC 1.1 over TCP), and send via TCP/IP DAT.

        Args:
            address (str): OSC address pattern, e.g. '/foo/bar'
            args (list|tuple): OSC arguments. Supports int, float, str, bytes/bytearray (blob),
                               bool (T/F), None (N), and nested lists/tuples (OSC arrays).
        """
        try:
            if not isinstance(address, str) or not address.startswith('/'):
                raise ValueError('OSC address must be a string starting with "/"')

            # Build OSC message bytes
            packet = self._build_osc_message(address, args or [])

            # SLIP-encode with double END framing per OSC 1.1 recommendation
            framed = self._slip_encode(packet)

            # Send raw bytes via TCP/IP DAT
            if hasattr(self.tcp, 'sendBytes'):
                self.tcp.sendBytes(framed)
            elif hasattr(self.tcp, 'send'):
                # Fallback: some builds may allow sending bytes through send()
                self.tcp.send(framed, terminator='')
            else:
                raise RuntimeError('TCP/IP DAT does not support sending bytes via Python API')

        except Exception as e:
            if hasattr(self, 'parent') and hasattr(self.parent, 'debug'):
                self.parent.debug(f"sendOSC error: {e}")
            else:
                print('sendOSC error:', e)

    def sendControlsToOSC(self):
        """Send OSC messages for each control using data from params_dat"""
        # Group parameters for faster processing and to avoid duplicates
        processed_controls = set()
        self.hideControls()

        # Process all parameters
        for row in range(1, self.parent.params_dat.numRows):
            param_name = self.parent.params_dat[row, 'name'].val
            control_type = self.parent.params_dat[row, 'control_type'].val
            if not control_type:
                continue
            control_index = int(
                self.parent.params_dat[row, 'control_index'].val)
            control_key = f"{control_type}{control_index}"

            # Skip if already processed (for paired controls like XY, RGB)
            if control_key in processed_controls:
                continue

            processed_controls.add(control_key)

            # Get parameter object
            par = self.parent.base_comp.par[param_name]
            if par is None:
                self.parent.debug(
                    f"Parameter {param_name} not found in {self.parent.base_comp} base component")
                continue

            # Extract values from params_dat
            name = self.parent.params_dat[row, 'label'].val
            x = self.parent.params_dat[row, 'x'].val
            y = self.parent.params_dat[row, 'y'].val
            width = self.parent.params_dat[row, 'width'].val
            height = self.parent.params_dat[row, 'height'].val
            mode = self.parent.params_dat[row, 'mode'].val

            if x == '':  # Skip if position is not set
                continue

            

            # Send control configuration
            self.sendOSC('/modify_control', [
                control_type,
                control_index,
                x, y,
                width, height,
                mode,
                self.menu_labels(par)
            ])
            
            if control_type != 'radio':
                # Send label position
                self.sendOSC('/modify_control', [
                    "label",
                    row,
                    x, y,
                    width, height,
                    "expression",
                    []
                ])

                # Send label text + size
                self.sendOSC('/label' + str(row), [name])

            # Send initial value
            self.parent.OnValueChange(par, None)  # This might trigger sendOSC internally, consider if delay is needed there too

            # Send color
            self.sendOSC('/color_control', [control_type, control_index, *self.config.color])

            self.parent.debug(
                f"Created control {control_type}{control_index} for {par.name}")
            
            if self.config.sleep_time > 0:
                time.sleep(self.config.sleep_time)

    def menu_labels(self, par) -> List[str]:  
        # For menus, send up to first 20 labels (TouchOSC limit)
        # Limit to first N chars of each label if needed
        if not par.isMenu:
            return []
        else:
            menuLabelLimit = self.menu_label_limit(par)
            if menuLabelLimit is not None:
                return [label[:menuLabelLimit] for label in par.menuLabels[:20]]
            return par.menuLabels[:20]

    def menu_label_limit(self, par):
        count = len(par.menuLabels)
        for threshold, limit in ((15, 3), (11, 4), (8, 5)):
            if count >= threshold:
                return limit
        return None

        
    def hideControls(self):
        for control_type, count in self.config.control_limits.items():
            for i in range(1, count + 1):
                self.sendOSC('/hide_control', [control_type, i])

    def OnReceiveOSC(self, dat, rowIndex, message, byteData, timeStamp, address, args, peer):
        try:
            if address == '/fadeTimeFader1':
                self.parent.debug(f"Fade time changed to {args[0]}")
                if self.parent.preset_manager and hasattr(self.parent.preset_manager, 'tauceti_manager'):
                    self.parent.preset_manager.tauceti_manager.par.Interacttime = float(args[0])*10
                return

            if address == '/Randomize/RandomAmount1':
                self.parent.debug(f"Random amount changed to {args[0]}")
                if self.parent.randomize_manager:
                    self.parent.randomize_manager.random_amount = float(args[0])
                return

            self.parent.debug(f"Received OSC message: {address} with args: {args}")
            control_name, control_type, index = self.parseAddress(address)

            if control_name is None:
                self.parent.debug(f"Cant parse OSC address. Ignoring message: {address}")
                return

            # Keep existing logic for preset buttons
            if control_name.startswith('PBUTTONS/'):
                if self.parent.preset_manager:
                    self.parent.preset_manager.recall_preset(index)
                return

            # Keep existing logic for randomize buttons
            if control_name.startswith('RBUTTONS/'):
                self.parent.debug(f"Randomize button {index} pressed")
                if self.parent.randomize_manager:
                    self.parent.randomize_manager.randomize(index)
                return

            param_name = self.find_parameter_by_control(control_type, index)
            if not param_name:
                self.parent.debug(f"Parameter not found for control {control_name}")
                return

            param = self.parent.base_comp.par[param_name]
            if param is None:
                self.parent.debug(f"Parameter {param_name} not found in base component")
                return

            # Use parameter manager to update parameter value
            self.parent.parameter_manager.update_parameter_value(param, args)
            self.parent.debug(f"Updated {param.name} to {args}")
        except Exception as e:
            self.parent.debug(f"Error handling OSC message: {e}")

    def parseAddress(self, address):
        control_name = address.lstrip('/')

        # Special case handling for PBUTTONS/ and RBUTTONS/
        if control_name.startswith('PBUTTONS/') or control_name.startswith('RBUTTONS/'):
            parts = control_name.split('/')
            if len(parts) == 2 and parts[1].isdigit():
                return control_name, parts[0], int(parts[1])

        # Find the transition between letters and digits
        prefix_end = 0
        for i, char in enumerate(control_name):
            if char.isdigit():
                prefix_end = i
                break

        # If no digits found or starts with digit, can't parse properly
        if prefix_end == 0 or prefix_end == len(control_name):
            self.parent.debug(f"Address format not recognized: {address}")
            return None, None, None

        control_type = control_name[:prefix_end]
        index_str = control_name[prefix_end:]
        try:
            index = int(index_str)
        except ValueError:
            self.parent.debug(f"Invalid index {index_str}")
            return None, None, None

        return control_name, control_type, index

    def find_parameter_by_control(self, control_type, index):
        """
        Find parameter name that corresponds to a specific control type and index

        Args:
            control_type (str): Type of control (fader, button, etc.)
            index (int): Index of the control

        Returns:
            str or None: Parameter name if found, None otherwise
        """
        for row in range(1, self.parent.params_dat.numRows):
            row_control_type = self.parent.params_dat[row, 'control_type'].val
            if not row_control_type:
                continue

            row_control_index = int(self.parent.params_dat[row, 'control_index'].val)
            if row_control_type == control_type and row_control_index == index:
                return self.parent.params_dat[row, 'name'].val

        return None

    def resetOSC(self):
        pass
        # self.udp.par.active = False
        # self.udp.par.active = True
        # self.osc_in.par.active = True
        # self.osc_in.par.active = False
        # self.tcp.par.active = True
        # self.tcp.par.active = False
        
        
    def OnReceiveOSC_TCP(self, incoming: bytes):
        """Accumulate TCP stream bytes, extract SLIP frames, and dispatch to OnReceiveOSC.

        Note: Wire this to the TCP/IP DAT's onReceive callback: call
              op('path/to/thisDAT').par.extension.feedTcpBytes(byteData)
        """
        if not hasattr(self, '_rx_buf'):
            self._rx_buf = bytearray()

        END = 0xC0
        ESC = 0xDB
        ESC_END = 0xDC
        ESC_ESC = 0xDD

        buf = self._rx_buf
        frame = bytearray()
        esc = False

        for byte in incoming:
            if esc:
                if byte == ESC_END:
                    frame.append(END)
                elif byte == ESC_ESC:
                    frame.append(ESC)
                else:
                    # Invalid escape, keep raw
                    frame.append(byte)
                esc = False
                continue

            if byte == ESC:
                esc = True
                continue

            if byte == END:
                if frame:
                    # Complete frame: decode OSC and route
                    try:
                        addr, argv = self._decode_osc_message(bytes(frame))
                        # Reuse existing OnReceiveOSC workflow
                        self.OnReceiveOSC(None, -1, None, None, None, addr, argv, None)
                    except Exception as e:
                        if hasattr(self.parent, 'debug'):
                            self.parent.debug(f'OSC decode error: {e}')
                    frame.clear()
                # else: ignore duplicate ENDs (framing flush)
                continue

            frame.append(byte)

        # Keep partial in buffer for next call
        buf[:] = frame
        
        
    # -----------------------
    # OSC encode/decode utils
    # -----------------------
    def _pad4(self, b: bytes) -> bytes:
        pad = (-len(b)) & 3
        return b + (b'\x00' * pad)

    def _pack_string(self, s: str) -> bytes:
        b = s.encode('utf-8') + b'\x00'
        return self._pad4(b)

    def _pack_blob(self, data: bytes) -> bytes:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError('Blob must be bytes or bytearray')
        b = bytes(data)
        return struct.pack('>i', len(b)) + self._pad4(b)

    def _pack_arg(self, a):
        """Return (typetag_str, encoded_bytes) for a single OSC argument."""
        if isinstance(a, bool):
            # T/F have no data payload
            return ('T' if a else 'F', b'')
        if a is None:
            return ('N', b'')
        if isinstance(a, int):
            # 32-bit int
            return ('i', struct.pack('>i', int(a)))
        if isinstance(a, float):
            return ('f', struct.pack('>f', float(a)))
        if isinstance(a, str):
            return ('s', self._pack_string(a))
        if isinstance(a, (bytes, bytearray)):
            return ('b', self._pack_blob(a))
        if isinstance(a, (list, tuple)):
            # OSC array: [ elements ]
            tags = ['[']
            data = []
            for el in a:
                t, d = self._pack_arg(el)
                tags.append(t)
                data.append(d)
            tags.append(']')
            return (''.join(tags), b''.join(data))
        # Fallback: coerce to string
        return ('s', self._pack_string(str(a)))

    def _build_osc_message(self, address: str, args) -> bytes:
        # address
        out = [self._pack_string(address)]

        # type tag string: starts with comma
        tags = [',']
        data_parts = []

        for a in (args or []):
            t, d = self._pack_arg(a)
            tags.append(t)
            data_parts.append(d)

        out.append(self._pack_string(''.join(tags)))
        out.append(b''.join(data_parts))
        return b''.join(out)

    # -----------------------
    # SLIP framing (RFC1055)
    # -----------------------
    def _slip_encode(self, payload: bytes) -> bytes:
        END = 0xC0
        ESC = 0xDB
        ESC_END = 0xDC
        ESC_ESC = 0xDD

        encoded = bytearray()
        # Leading END to flush any line noise per OSC 1.1 guidance
        encoded.append(END)
        for b in payload:
            if b == END:
                encoded.extend((ESC, ESC_END))
            elif b == ESC:
                encoded.extend((ESC, ESC_ESC))
            else:
                encoded.append(b)
        # Trailing END marks frame boundary
        encoded.append(END)
        return bytes(encoded)

    def _read_padded_string(self, data: bytes, off: int):
        end = data.find(b'\x00', off)
        if end == -1:
            raise ValueError('OSC string not null-terminated')
        s = data[off:end].decode('utf-8', errors='ignore')
        # advance to next 4-byte boundary after the null
        off = (end + 4) & ~3
        return s, off

    def _decode_osc_message(self, data: bytes):
        """Decode a single OSC message (no bundles) into (address, args)."""
        off = 0
        address, off = self._read_padded_string(data, off)
        typetags, off = self._read_padded_string(data, off)
        if not typetags or typetags[0] != ',':
            raise ValueError('Invalid OSC typetag string')

        args = []
        i = 1
        # Support minimal set: i, f, s, b, T, F, N, arrays [ ]
        def read_i():
            nonlocal off
            val = struct.unpack_from('>i', data, off)[0]
            off += 4
            return val
        def read_f():
            nonlocal off
            val = struct.unpack_from('>f', data, off)[0]
            off += 4
            return val
        def read_s():
            nonlocal off
            s, off2 = self._read_padded_string(data, off)
            off = off2
            return s
        def read_b():
            nonlocal off
            n = struct.unpack_from('>i', data, off)[0]
            off += 4
            blob = data[off:off+n]
            off = (off + n + 3) & ~3
            return blob

        def read_array():
            nonlocal i
            arr = []
            i += 1
            while i < len(typetags) and typetags[i] != ']':
                t = typetags[i]
                if t == 'i': arr.append(read_i())
                elif t == 'f': arr.append(read_f())
                elif t == 's': arr.append(read_s())
                elif t == 'b': arr.append(read_b())
                elif t == 'T': arr.append(True)
                elif t == 'F': arr.append(False)
                elif t == 'N': arr.append(None)
                elif t == '[':
                    arr.append(read_array())
                else:
                    # unsupported, skip
                    pass
                i += 1
            return arr

        while i < len(typetags):
            t = typetags[i]
            if t == 'i': args.append(read_i())
            elif t == 'f': args.append(read_f())
            elif t == 's': args.append(read_s())
            elif t == 'b': args.append(read_b())
            elif t == 'T': args.append(True)
            elif t == 'F': args.append(False)
            elif t == 'N': args.append(None)
            elif t == '[':
                args.append(read_array())
            else:
                # unsupported typetag: ignore
                pass
            i += 1

        return address, args
