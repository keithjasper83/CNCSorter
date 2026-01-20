# Disabled Features

## Tkinter Touchscreen Interface

**Status:** Disabled / Removed
**Original File:** `src/gui_touchscreen.py` (renamed to `src/gui_touchscreen.py.backup` during merge)
**Reason:** Replaced by NiceGUI-based interface (`src/touchscreen_interface.py`).

### Specification

The disabled interface was a Tkinter-based GUI optimized for Raspberry Pi touchscreen usage (800x480). It provided the following functionality:
- Fullscreen window with large touch-friendly buttons.
- Vision System control (Start/Stop camera).
- CNC Controller connection (Serial/HTTP).
- Bed Mapping workflow (New Map, Capture, Stitch, Save).
- System status display (CNC position, object counts).

The code relied on `tkinter`, `infrastructure.vision`, `infrastructure.cnc_controller`, `application.bed_mapping`, and `domain.entities`.

This feature is considered obsolete in favor of the web-based NiceGUI implementation which offers better remote access and modern UI capabilities.
