# XWM X-window-manager
A simple floating window manager written in python and xlib.

Free to use or modify - just for fun

Requires:
- python3
- python3-xlib
- python3-ewmh
- xdotool
- xterm
- xfonts (font lucida is used)
- python3-pil (optional - for screenshots)

Very minimal:
- close button (the red one)
- maximize button (the green one)
- window moving (from the titlebar or with shortcut Alt+LMB)
- window resizing (left click in the bottom right corner of the window; if the pointer changes, just drag)
- menu (right click in the background; two options: execute xterm or exit from the wm)
- dock on top right:
    - right click in the text XWM to bring it to top
    - left click in an item (if any) to bring that window on top, also if it is minimized
    - right click in an item (if any) to have a kind of minimization, or restore it to top
- splash windows are undecorated
- etc.

Because this wm is minimal, many things are left out, and maybe never will be implemented. This wm has no options, unless changing the options in the code (mostly unsupported).

Not any other docks can interoperate with the wm.

Keybindings:
- alt+LMB to move the window;
- alt+d to bring up the dock;
- alt+STAMP to get the screenshot of the whole screen (python3-pil is required); the screenshot will be saved in the user home dir.

No virtual desktops.

To test this wm:
- from a terminal: Xephyr :1 -screen 1366x768
- from another terminal: DISPLAY=:1 xterm &
- launch the wm from that xterm
- or just execute/use it as any wm.

The newer version has more features and fixes.

![My image](https://github.com/frank038/XWM-X-window-manager-/blob/main/screenshot.png)
