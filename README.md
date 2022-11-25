# XWM X-window-manager
A simple stacking window manager written in python end xlib.

Free to use or modify

Requires:
- python3
- xlib
- python3-ewmh
- xdotool
- xterm
- xfonts (font lucida is used)

Very minimal:
- close button (the red one)
- maximize button (the green one)
- window moving (from the titlebar)
- window resizing (click in the bottom right corner of the window, if the pointer change just drag)
- menu (right click in the background; two options: execute xterm or exit from the wm)
- dock on top right:
    - right click in the text XWM to bring it to top
    - left click in an item (if any) to bring that window on top, also if it is minimized
    - right click in an item (if any) to have a kind of minimization, or restore it to top
- splash windows are undecorated
- etc.

Because this wm is minimal, many things are left out, and maybe never will be implemented. This wm has no options, unless changing the code (mostly unsupported).

No docks can interoperate with the wm.

No keybindings. No virtual desktops.

To test this wm:
- from a terminal: Xephyr :1 -screen 1366x768
- from another terminal: DISPLAY=:1 xterm &
- launch the wm from that terminal
- or just execut it as any wm.

![My image](https://github.com/frank038/XWM-X-window-manager-/blob/main/screenshot.png)
