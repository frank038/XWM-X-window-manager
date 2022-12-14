#!/usr/bin/env python3

# 20221214_01

import os
import subprocess
import sys
import time
import signal

from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont

from ewmh import EWMH
ewmh = EWMH()

LEFT_PTR = Xcursorfont.left_ptr
RIGHT_CORNER_BOTTOM = Xcursorfont.bottom_right_corner

_display = Display()

MAIN_DOCK_HEIGHT = 0

# physical screen size
screen_width = Display().screen().width_in_pixels
screen_height = Display().screen().height_in_pixels
# usable screen size
screen_width_usable = screen_width
screen_height_usable = screen_height - MAIN_DOCK_HEIGHT
# usable screen x and y
start_x = 0
end_x = screen_width_usable
start_y = 0
end_y = screen_height_usable

_create_dock = 1
_is_running = 1

TITLE_HEIGHT = 24
DECO_COLOR = 'chocolate3'
TITLE_FONT = '-*-lucida-medium-r-normal-*-24-*-*-*-*-*-*-*'
BORDER_WIDTH = 3
colormap = Display().screen().default_colormap
win_color = colormap.alloc_named_color(DECO_COLOR).pixel

dock_width = 200
# do not change
dock_height = 50
DOCK_FONT = '-*-lucida-medium-r-normal-*-34-*-*-*-*-*-*-*'
 
BUTTON_SIZE = 20
BUTTON_CLOSE_COLOR = 'brown4'
close_color = colormap.alloc_named_color(BUTTON_CLOSE_COLOR).pixel
BUTTON_MAXIMIZE_COLOR = 'DarkGreen'
maxi_color = colormap.alloc_named_color(BUTTON_MAXIMIZE_COLOR).pixel
BUTTON_MINIMIZE_COLOR = 'DarkOrange4'
mini_color = colormap.alloc_named_color(BUTTON_MINIMIZE_COLOR).pixel

dock_border_color = colormap.alloc_named_color('DarkGreen').pixel
dock_border_color_min = colormap.alloc_named_color('gray80').pixel

# Alt modifier code - 64 - 133
ALT_KEY = 64

_SCREENSHOT = 1
if _SCREENSHOT:
    # stamp key code
    STAMP_KEY = 107

# dock key
DOCK_KEY = "d"

# menu key
MENU_KEY = "m"

# windows with decoration: window:decoration
DECO_WIN = {}

# a window is desktop type
desktop_window = None
# windows that are dock type
dock_windows = []

all_windows = []
all_windows_stack = []
# the program not the wm
active_window = None

# windows in maximized state: window:[prev_win_x, prev_win_y, win_unmaximized_width, win_unmaximized_height]
MAXIMIZED_WINDOWS = {}

WINDOW_WITH_DECO = [
"_NET_WM_WINDOW_TYPE_UTILITY",
"_NET_WM_WINDOW_TYPE_DIALOG",
"_NET_WM_WINDOW_TYPE_NORMAL"]

WINDOW_WITH_NO_DECO = [
'_NET_WM_WINDOW_TYPE_TOOLBAR',
'_NET_WM_WINDOW_TYPE_MENU',
'_NET_WM_WINDOW_TYPE_DND',
'_NET_WM_WINDOW_TYPE_DROPDOWN_MENU',
'_NET_WM_WINDOW_TYPE_COMBO',
'_NET_WM_WINDOW_TYPE_POPUP_MENU']

WINDOWS_MAPPED_WITH_NO_DECO = [
'_NET_WM_WINDOW_TYPE_DOCK',
'_NET_WM_WINDOW_TYPE_DESKTOP',
'_NET_WM_WINDOW_TYPE_SPLASH',
'_NET_WM_WINDOW_TYPE_NOTIFICATION']


def signal_catch(signal, frame):
    print("\nCTRL+C or KILL - exiting...")
    _is_running = 0
    # time.sleep(1)
    sys.exit(0)

# ctrl+c
signal.signal(signal.SIGINT, signal_catch)
# term or kill
signal.signal(signal.SIGTERM, signal_catch)


def root_cursor_normal():
    font = _display.open_font('cursor')
    # black with white border
    cursor = font.create_glyph_cursor(font, LEFT_PTR, LEFT_PTR+1, (0, 0, 0), (65535, 65535, 65355))
    _display.screen().root.change_attributes(cursor=cursor)
    _display.flush()
    
root_cursor_normal()


def root_cursor_right_corner_bottom():
    font = _display.open_font('cursor')
    # black with white border
    cursor = font.create_glyph_cursor(font, RIGHT_CORNER_BOTTOM, RIGHT_CORNER_BOTTOM+1, (0, 0, 0), (65535, 65535, 65355))
    _display.screen().root.change_attributes(cursor=cursor)
    _display.flush()
    
DECO_EXPOSURE = 1

if DECO_EXPOSURE:
    mask_deco = X.EnterWindowMask | X.LeaveWindowMask | X.ExposureMask
else:
    mask_deco = X.EnterWindowMask | X.LeaveWindowMask


if _SCREENSHOT:
    
    try:
        from PIL import Image
    except:
        _SCREENSHOT = 0
    
    def take_screenshot(x,y,w,h):
        root = _display.screen().root
        raw = root.get_image(x, y, w, h, X.ZPixmap, 0xffffffff)
        if isinstance(raw.data,str):
            bytes=raw.data.encode()
        else:
            bytes=raw.data
        image = Image.frombytes("RGB", (w, h), bytes, "raw", "BGRX")
        image.save(os.path.join(os.path.expanduser('~'), "screenshot_{}.png".format( time.ctime(time.time()) )))

###################


class x_wm:
    
    def __init__(self):
        #
        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.display.screen().root
        #
        self.NET_WM_STATE = self.display.intern_atom("_NET_WM_STATE")
        self.NET_STATE = self.display.intern_atom("_NET_STATE")
        self.NET_WM_NAME = self.display.intern_atom('_NET_WM_NAME')
        self.WM_NAME = self.display.intern_atom('WM_NAME')
        self.WM_FULLSCREEN = self.display.intern_atom("_NET_WM_STATE_FULLSCREEN")
        self.WM_MAXIMIZED_HORZ = self.display.intern_atom("_NET_WM_STATE_MAXIMIZED_HORZ")
        self.WM_MAXIMIZED_VERT = self.display.intern_atom("_NET_WM_STATE_MAXIMIZED_VERT")
        self.WM_HIDDEN = self.display.intern_atom("_NET_WM_STATE_HIDDEN")
        #
        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask
                | X.EnterWindowMask | X.LeaveWindowMask | X.FocusChangeMask
                | X.ButtonPressMask | X.ButtonReleaseMask 
                | X.KeyPressMask | X.KeyReleaseMask)
               # | X.PropertyChangeMask)
        
        self.root.change_attributes(event_mask=mask)
        #
        # grab alt key globally
        self._is_alt = 1
        def _alt_key():
            self._is_alt = 0
        
        self.root.grab_key(ALT_KEY,
            X.AnyModifier, 1, X.GrabModeAsync, X.GrabModeAsync, onerror=_alt_key)
        
        # grab stamp key globally
        if _SCREENSHOT:
            self.root.grab_key(STAMP_KEY,
                X.Mod1Mask, 1, X.GrabModeAsync, X.GrabModeAsync)
        
        # dock
        self.root.grab_key(self.display.keysym_to_keycode(XK.string_to_keysym(DOCK_KEY)),
            X.Mod1Mask, 1, X.GrabModeAsync, X.GrabModeAsync)
        
        # the window that grabbed button 1
        self.window_button1_grab = None
        #
        # window move event
        self.mouse_button_left = 0
        self.delta_drag_start_point = None
        # window resize event
        self.mouse_button_left_resize = 0
        # also change the cursor image - 1 right 2 left
        self.mouse_button_resize_window = 0
        self.mouse_button_resize_drag_start_point = None
        self.window_resize_geometry = None
        # cursor change for resizing if at bottom right
        self.cursor_resize_bottom_right_changed = 0
        #
        self.window_maximized = 0
        # only one can be in this state
        self.window_in_fullscreen_state = []
        self.window_in_fullscreen_state_CM = []
        #
        self.close_btn_pressed = 0
        self.maxi_btn_pressed = 0
        # create the wm dock
        self._dock = None
        if _create_dock:
            self.wm_dock()
            self.dock_width = dock_width
            self.dock_height = dock_height
        # program window:[state]
        self.dock_items = {}
        # the menu
        self._m = None
        #
        self.main_loop()
    

    # the menu
    def _menu(self, x, y):
        mwidth = 200
        mheight = 100
        mx = x
        my = y
        #
        if mx + mwidth > screen_width_usable:
            mx = screen_width_usable - mwidth - 2
        #
        if my + mheight > screen_height_usable:
            my = screen_height_usable - mheight - 2
        #
        self._m = self.screen.root.create_window(
            mx,
            my,
            mwidth,
            mheight,
            1,
            self.screen.root_depth,
            X.InputOutput,
            background_pixel=win_color,
            override_redirect=1,
        )
        #
        self._m.grab_button(1, X.NONE, True,
                 X.ButtonPressMask, X.GrabModeAsync,
                 X.GrabModeAsync, X.NONE, X.NONE)
        self._m.map()
        #
        font = self.display.open_font(TITLE_FONT)
        menu_gc = self._m.create_gc(font=font, foreground=self.screen.black_pixel, line_width=2)
        # 
        name = "XTERM"
        pos_x = 10
        pos_y = 30
        self._m.draw_text(menu_gc, pos_x, pos_y, name)
        self._m.line(menu_gc, 0, pos_y+20, mwidth, pos_y+20)
        #
        name = "Exit"
        self._m.draw_text(menu_gc, pos_x, pos_y+50, name)
        
    
    def prog_execute(self, prog):
        try:
            os.system("{} &".format(prog))
        except:
            pass
    
    # 
    def on_dock_items(self):
        if not _create_dock:
            return
        # 
        d_geom = self._dock.get_geometry()
        # clean everything
        if d_geom.height > dock_height:
            self._dock.clear_area(0, dock_height, dock_width, screen_height)
        # and resize back
        self._dock.configure(width=dock_width, height=dock_height)
        self.dock_height = dock_height
        #
        len_items = len(self.dock_items)
        if len_items:
            self.dock_height += 50 * len_items
            self._dock.configure(width=dock_width, height=self.dock_height)
        #
        font = self.display.open_font(TITLE_FONT)
        self.on_dock_items_f(None, self.dock_items)
    
    def on_dock_items_f(self, len_items, temp_list):
        d_geom = self._dock.get_geometry()
        # clean everything
        if d_geom.height > dock_height:
            self._dock.clear_area(0, dock_height, dock_width, screen_height)
        font = self.display.open_font(TITLE_FONT)
        item_gc = self._dock.create_gc(font=font, foreground=dock_border_color, line_width=1)
        i = 0
        for k,v in temp_list.items():
            item_name = self.get_window_class(k)
            self._dock.draw_text(item_gc, 8, int(4+dock_height+i*50+17+11), item_name)
            if v[0] == 0:
                self._dock.rectangle(item_gc, 4, 4+dock_height+i*50, dock_width-9, 50-9)
            elif v[0] == 1:
                item_gc.change(foreground=dock_border_color_min)
                self._dock.rectangle(item_gc, 4, 4+dock_height+i*50, dock_width-9, 50-9)
                item_gc.change(foreground=dock_border_color)
            self.dock_items[k] = [v[0], i]
            i += 1
    
    def wm_dock(self):
        x = end_x-dock_width
        y = 0
        self._dock = self.screen.root.create_window(
            x,
            y,
            dock_width,
            dock_height,
            1,
            self.screen.root_depth,
            X.InputOutput,
            background_pixel=win_color,
            override_redirect=1,
        )
        #
        self._dock.grab_button(1, X.NONE, True,
                 X.ButtonPressMask, X.GrabModeAsync,
                 X.GrabModeAsync, X.NONE, X.NONE)
        #
        mask = X.EnterWindowMask | X.LeaveWindowMask | X.ExposureMask
        self._dock.change_attributes(event_mask=mask)
        #
        self._dock.map()
        #
        self.dock_content()
        
    def dock_content(self):
        # inner border
        dock_gc = self._dock.create_gc(foreground=dock_border_color, line_width=3)
        self._dock.rectangle(dock_gc, 4, 4, dock_width-9, dock_height-9)
        #
        font2 = self.display.open_font(DOCK_FONT)
        fq2 = font2.query_text_extents(b"XWM")
        name_width = fq2._data['overall_left'] + fq2._data['overall_right']
        name_height = fq2._data['overall_ascent'] + fq2._data['overall_descent']
        title_gc = self._dock.create_gc(font=font2, foreground=self.screen.black_pixel)
        name = "XWM"
        pos_x = int((dock_width-name_width)/2)
        pos_y = int((name_height+(dock_height-name_height)/2))
        self._dock.draw_text(title_gc, pos_x, pos_y, name)
        
    
    def getProp(self, win, prop):
        try:
            prop = win.get_full_property(self.display.intern_atom('_NET_WM_' + prop), X.AnyPropertyType)
            if prop:
                return prop.value.tolist()
            return None
        except:
            return None
    
    def get_window_name(self, window):
        try:
            prop = window.get_full_property(self.display.intern_atom("_NET_WM_NAME"), X.AnyPropertyType)
            if prop:
                return prop.value.decode()
            else:
                prop = window.get_full_property(self.display.intern_atom("WM_NAME"), X.AnyPropertyType)
                if prop:
                    return prop.value.decode()
                else:
                    return "X"
                return "X"
        except:
            return "X"
    
    def get_window_class(self, window):
        try:
            cmd, cls = window.get_wm_class()
        except:
            return "X"
        if cls is not None:
            return cls
        else:
            return "X"
    
    def get_window_type(self, window):
        try:
            prop = window.get_full_property(self.display.get_atom("_NET_WM_WINDOW_TYPE"), X.AnyPropertyType)
            if prop:
                return prop.value.tolist()
            else:
                return 1
        except:
            return 1
    
    
    # add a decoration to win
    def win_deco(self, win):
        geom = win.get_geometry()
        DECO_WIDTH = geom.width+BORDER_WIDTH*2-2
        DECO_HEIGHT = geom.height+BORDER_WIDTH+TITLE_HEIGHT-2
        deco = self.screen.root.create_window(
            geom.x-BORDER_WIDTH,
            geom.y-TITLE_HEIGHT,
            DECO_WIDTH,
            DECO_HEIGHT,
            0,
            self.screen.root_depth,
            X.InputOutput,
            background_pixel=win_color,
            override_redirect=1,
        )
        deco.configure(border_width=1)
        #
        deco.grab_button(1, X.NONE, True,
                 X.ButtonPressMask, X.GrabModeAsync,
                 X.GrabModeAsync, X.NONE, X.NONE)
        #
        deco.change_attributes(event_mask=mask_deco)
        #
        global DECO_WIN
        DECO_WIN[win] = deco
        # needed by the title name
        deco.map()
        #
        self.refresh_title(win, deco)
        
    # title window
    def win_deco_title(self, deco, name):
        font = self.display.open_font(TITLE_FONT)
        title_gc = deco.create_gc(font=font, foreground=self.screen.black_pixel)
        # title text
        geom = deco.get_geometry()
        deco.clear_area(BORDER_WIDTH, 0, geom.width, TITLE_HEIGHT)
        #
        pos_x = BORDER_WIDTH+2
        pos_y = 18
        deco.draw_text(title_gc, pos_x, pos_y, name)
        #
        self.draw_btn(deco, geom.width-BUTTON_SIZE-8, int((TITLE_HEIGHT-BUTTON_SIZE)/2)-1, "close")
        self.draw_btn(deco, geom.width-BUTTON_SIZE*2-10, int((TITLE_HEIGHT-BUTTON_SIZE)/2-1), "maxi")
        # self.draw_btn(deco, geom.width-BUTTON_SIZE*3-10, int((TITLE_HEIGHT-BUTTON_SIZE)/2-1), "mini")
        
    # draw the titlebar buttons
    def draw_btn(self, deco, x, y, type):
        if type == "close":
            btn_gc = deco.create_gc(foreground=close_color)
            # deco.fill_arc(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE, 0, 360 * 64)
            deco.fill_rectangle(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE)
        elif type == "maxi":
            btn_gc = deco.create_gc(foreground=maxi_color)
            # deco.fill_arc(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE, 0, 360 * 64)
            deco.fill_rectangle(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE)
        # elif type == "mini":
            # btn_gc = deco.create_gc(foreground=mini_color)
            # # deco.fill_arc(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE, 0, 360 * 64)
            # deco.fill_rectangle(btn_gc, x, y, BUTTON_SIZE, BUTTON_SIZE)
    
    # close window
    def close_window(self, win):
        winPid = None
        try:
            winPid = ewmh.getWmPid(win)
        except:
            pass
        if winPid:
            try:
                # 9 signal.SIGKILL - 15 signal.SIGTERM
                # os.kill(winPid[0], 15)
                os.kill(winPid, 15)
            except:
                return
        else:
            try:
                ret = os.system("xdotool windowclose {}".format(win.id))
                if ret != 0:
                    ret = os.system("xdotool windowkill {}".format(win.id))
                    if ret != 0:
                        return
            except:
                return
        #
        if win in MAXIMIZED_WINDOWS:
            del MAXIMIZED_WINDOWS[win]
    
    # maximize the window
    def maximize_window(self, deco):
        win = self.find_win_of_deco(deco)
        #
        if not win in MAXIMIZED_WINDOWS:
            wgeom = win.get_geometry()
            MAXIMIZED_WINDOWS[win] = [wgeom.x, wgeom.y, wgeom.width, wgeom.height]
            #
            x = start_x
            y = start_y
            width = screen_width_usable
            height = screen_height_usable
            deco = DECO_WIN[win]
            deco.configure(x=x, y=y, width=width,height=height)
            win.configure(x=x+BORDER_WIDTH+1, y=y+TITLE_HEIGHT+1, 
                width=width-BORDER_WIDTH*2-1, height=height-TITLE_HEIGHT-BORDER_WIDTH-2)
            # refresh the title
            self.refresh_title(win, deco)
        else:
            data = MAXIMIZED_WINDOWS[win]
            x = data[0]
            y = data[1]
            width = data[2]
            height = data[3]
            #
            deco.configure(x=x-BORDER_WIDTH-1,y=y-TITLE_HEIGHT-1,
                width=width+BORDER_WIDTH*2, height=height+TITLE_HEIGHT+BORDER_WIDTH)
            win.configure(x=x,y=y,width=width,height=height)
            #
            del MAXIMIZED_WINDOWS[win]
            # refresh the title
            self.refresh_title(win, deco)
    
    # find the window decoration of the given window win
    def find_win_of_deco(self, deco):
        win = None
        for k,v in DECO_WIN.items():
            if v == deco:
                win = k
                break
        #
        return win
    
    
    def refresh_title(self, win, deco):
        if not win:
            return
        if not deco:
            return
        if win == self._dock or deco == self._dock:
            return
        if win == self._m or deco == self._m:
            return
        #
        win_name = self.get_window_class(win)
        self.win_deco_title(deco, win_name)
    
    
    def main_loop(self):
        global active_window
        #
        while _is_running:
            #
            event = self.root.display.next_event()
            #
            if event.type == X.MapNotify:
                attrs = event.window.get_attributes()
                if attrs is None:
                    continue
                #
                # not to be managed by window manager
                if attrs.override_redirect:
                    continue
                # skip the dock
                if event.window == self._dock:
                    continue
                # skip the menu
                if event.window == self._m:
                    continue
                #
                if event.window in all_windows:
                    continue
                if event.window in all_windows_stack:
                    continue
                # skip decorations
                is_found = 0
                for k,v in DECO_WIN.items():
                    if v == event.window:
                        is_found = 1
                        break
                    continue
                if is_found:
                    continue
                #
                all_windows.append(event.window)
                all_windows_stack.append(event.window)
                #
                if not event.window in self.dock_items:
                    self.dock_items[event.window] = [0]
                    self.on_dock_items()
                #
                # event.window.change_attributes(event_mask=X.PropertyChangeMask)
                #
                # set the active window
                if event.window in DECO_WIN:
                    active_window = event.window
            
            #
            elif event.type == X.MapRequest:
                #
                attrs = event.window.get_attributes()
                if attrs is None:
                    continue
                # not to be managed by window manager
                if attrs.override_redirect:
                    continue
                # windows that do not need decoration
                ew_type = ewmh.getWmWindowType(event.window, str=True)
                #
                if ew_type and ew_type[0] in WINDOW_WITH_NO_DECO:
                    continue
                #
                if event.window in DECO_WIN:
                    continue
                # remove the border from the program
                event.window.change_attributes(
                         border_pixel=win_color,
                         border_width=0)
                # center the window
                win_geom = event.window.get_geometry()
                x = int((screen_width-win_geom.width)/2)
                y = int((screen_height-win_geom.height)/2)
                event.window.configure(x=x, y=y)
                #
                # skip the decoration for these types of windows
                if ew_type and ew_type[0] in WINDOWS_MAPPED_WITH_NO_DECO:
                    event.window.map()
                    event.window.raise_window()
                    continue
                #
                # create the decoration
                self.win_deco(event.window)
                #
                deco = DECO_WIN[event.window]
                DECO_WIN[event.window].raise_window()
                event.window.raise_window()
                event.window.map()
                #
                # deco must be mapped
                self.refresh_title(event.window, deco)
            
            #
            # first unmap then destroy eventually
            elif event.type == X.DestroyNotify:
                if event.window in DECO_WIN:
                    DECO_WIN[event.window].destroy()
                    del DECO_WIN[event.window]
                    #
                    if event.window in all_windows:
                        all_windows.remove(event.window)
                    if event.window in all_windows_stack:
                        all_windows_stack.remove(event.window)
                    #
                    if event.window in self.window_in_fullscreen_state:
                        self.window_in_fullscreen_state = []
                    if event.window in self.window_in_fullscreen_state_CM:
                        self.window_in_fullscreen_state_CM = []
                    #
                    if active_window == event.window:
                        active_window = None
                        # find another suitable window to set as active
                        if len(all_windows_stack) > 0:
                            iitem = all_windows_stack[-1]
                            if iitem not in dock_windows and iitem != desktop_window:
                                if iitem in DECO_WIN:
                                    DECO_WIN[iitem].raise_window()
                                    iitem.raise_window()
                                    active_window = iitem
                                    # refresh the title
                                    self.refresh_title(iitem, DECO_WIN[iitem])
                #
                if event.window in self.dock_items:
                    del self.dock_items[event.window]
                    self.on_dock_items()
            #
            elif event.type == X.ConfigureRequest:
                if self.mouse_button_left:
                    continue
                #
                window = event.window
                x, y = event.x, event.y
                width, height = event.width, event.height
                mask = event.value_mask
                #
                if mask in [0b1111,0b1100,0b0011,0b01000000]:
                    # window restore from fullscreen state
                    if self.window_in_fullscreen_state:
                        if event.window == self.window_in_fullscreen_state[0]:
                            if event.sequence_number == self.window_in_fullscreen_state[1]:
                                continue
                            if width == screen_width and height == screen_height:
                                self.window_in_fullscreen_state = []
                                continue
                            #
                            event.window.configure(x=x, y=y, width=width, height=height)
                            DECO_WIN[event.window].map()
                            DECO_WIN[event.window].raise_window()
                            event.window.raise_window()
                            self.refresh_title(event.window, DECO_WIN[event.window])
                            # self.window_in_fullscreen_state = []
                            continue
                    # fullscreen
                    if width == screen_width and height == screen_height:
                        if self.window_in_fullscreen_state_CM:
                            continue
                        # skip unwanted request - mpv hack?
                        if self.window_in_fullscreen_state:
                            if event.window == self.window_in_fullscreen_state[0]:
                                continue
                        #######
                        if event.window in DECO_WIN:
                            DECO_WIN[event.window].unmap()
                        event.window.raise_window()
                        event.window.configure(x=0, y=0, width=width, height=height)
                        self.window_in_fullscreen_state = [event.window, event.sequence_number]
                        continue
                    else:
                        #
                        event.window.configure(x=x, y=y, width=width+2, height=height+2)
                        #
                        if event.window in DECO_WIN:
                            DECO_WIN[event.window].configure(x=x-BORDER_WIDTH, y=y-TITLE_HEIGHT, 
                                width=width+BORDER_WIDTH*2, height=height+TITLE_HEIGHT+BORDER_WIDTH)
                            # write the window title
                            self.refresh_title(event.window, DECO_WIN[event.window])
                
            #
            elif event.type == X.Expose:
                if event.window == self._m:
                    continue
                #
                elif event.window == self._dock:
                    self.dock_content()
                    self.on_dock_items_f(len(self.dock_items), self.dock_items)
                else:
                    win = self.find_win_of_deco(event.window)
                    # if active_window:
                    if win in DECO_WIN:
                        if win != active_window:
                            self.refresh_title(win, event.window)
                    
            #
            elif event.type == X.EnterNotify:
                pass
                
            #
            elif event.type == X.PropertyNotify:
                # window and atom
                if event.atom in [self.WM_NAME, self.NET_WM_NAME]:
                    wname = self.get_window_name(event.window)
            
            #
            elif event.type == X.ClientMessage:
                #
                if event.client_type == self.NET_WM_STATE:
                    fmt, data = event.data
                    #
                    if fmt == 32 and data[1] == self.WM_FULLSCREEN:
                        if self.window_in_fullscreen_state:
                            continue
                        if data[0] == 1:
                            if not self.window_in_fullscreen_state_CM:
                                DECO_WIN[event.window].unmap()
                                event.window.raise_window()
                                self.window_in_fullscreen_state_CM = [event.window, event.window.get_geometry()]
                                event.window.configure(x=0, y=0, width=screen_width, height=screen_height)
                                # self.window_in_fullscreen_state = 1
                        elif data[0] == 0:
                            if self.window_in_fullscreen_state_CM:
                                if event.window == self.window_in_fullscreen_state_CM[0]:
                                    geom = self.window_in_fullscreen_state_CM[1]
                                    event.window.configure(x=geom.x, y=geom.y, width=geom.width, height=geom.height)
                                    DECO_WIN[event.window].map()
                                    DECO_WIN[event.window].raise_window()
                                    event.window.raise_window()
                                    self.refresh_title(event.window, DECO_WIN[event.window])
                                    self.window_in_fullscreen_state_CM = []
                                    # self.window_in_fullscreen_state = []
                    # maximize
                    if fmt == 32 and data[1] == self.WM_MAXIMIZED_VERT and data[2] == self.WM_MAXIMIZED_HORZ:
                        if data[0] == 1:
                            if event.window in DECO_WIN:
                                self.maximize_window(DECO_WIN[event.window])
                    # minimize
                    if fmt == 32 and data[1] == self.WM_HIDDEN:
                        if data[0]:
                            pass
            
            #
            elif event.type == X.MotionNotify:
                x = event.root_x
                y = event.root_y
                # 
                if self.mouse_button_left:
                    # window resize action - from right
                    if self.mouse_button_resize_window == 1:
                        for child, deco in DECO_WIN.items():
                            if deco == event.window:
                                ww = self.window_resize_geometry[2] + (x-self.mouse_button_resize_drag_start_point[0])
                                hh = self.window_resize_geometry[3] + (y-self.mouse_button_resize_drag_start_point[1])
                                #
                                xx = 0
                                yy = 0
                                # the width or the eight of any window must be at least 50
                                if ww > 50 or hh > 50:
                                    # width and height
                                    deco.configure(width=ww, height=hh)
                                    child.configure(width=ww-BORDER_WIDTH*2+2, height=hh-BORDER_WIDTH-TITLE_HEIGHT+2)
                                    # refresh the title
                                    self.refresh_title(child, deco)
                                break
                    # window drag action
                    else:
                        if active_window:
                            if self.close_btn_pressed or self.maxi_btn_pressed:
                                continue
                            #
                            win = active_window
                            deco = DECO_WIN[active_window]
                            #### unmaximize first
                            #
                            xx = 0
                            if win in MAXIMIZED_WINDOWS:
                                # skip if not the titlebar
                                if y > (start_y + TITLE_HEIGHT):
                                    continue
                                if (y - self.delta_drag_start_point[1]) > 3:
                                    data = MAXIMIZED_WINDOWS[win]
                                    yy = start_y + int(TITLE_HEIGHT/2)
                                    MAXIMIZED_WINDOWS[win] = [x-data[2], (y - self.delta_drag_start_point[1]+yy), data[2], data[3]]
                                    self.maximize_window(deco)
                                    xx = x-int(data[2]/2)
                                    deco.configure(x=xx)
                                    win.configure(x=xx+BORDER_WIDTH)
                                    self.refresh_title(win, deco)
                                    self.delta_drag_start_point = [x-xx, yy]
                            #
                            if not self.delta_drag_start_point:
                                continue
                            #
                            deco.configure(x=x - self.delta_drag_start_point[0], y=y - self.delta_drag_start_point[1])
                            win.configure(x=x - self.delta_drag_start_point[0]+BORDER_WIDTH, y=y - self.delta_drag_start_point[1] + TITLE_HEIGHT)
                            # refresh the title
                            self.refresh_title(win, deco)
            
            # 
            elif event.type == X.ButtonPress:
                #
                if self.window_button1_grab:
                    if self.window_button1_grab in DECO_WIN:
                        geom = DECO_WIN[self.window_button1_grab].get_geometry()
                        cx = geom.x
                        cy = geom.y
                        x = event.root_x
                        y = event.root_y
                        self.delta_drag_start_point = (x - cx, y - cy)
                    continue
                #
                # left mouse button
                if event.detail == 1:
                    # event.child is the deco or dock
                    if event.child != X.NONE:
                        if event.child == self._dock:
                            geom = event.child.get_geometry()
                            py = event.root_y
                            # items in the dock
                            if py > dock_height:
                                n_item = int((event.root_y-dock_height)/50)
                                win = None
                                _v = None
                                # bring the program to top if minimized
                                for k,v in self.dock_items.items():
                                    if v[1] == n_item:
                                        win = k
                                        _v = v
                                        break
                                #
                                if win and _v[0]:
                                    DECO_WIN[win].map()
                                    win.map()
                                    self.dock_items[win] = [0, v[1]]
                                    DECO_WIN[win].raise_window()
                                    win.raise_window()
                                    self.refresh_title(win, DECO_WIN[win])
                                    self.dock_items[win] = [0, _v[1]]
                                    self.on_dock_items_f(None, self.dock_items)
                                    active_window = win
                                    #
                                    continue
                                #########
                                if active_window == win:
                                    continue
                                else:
                                    # bring to top
                                    deco = DECO_WIN[win]
                                    deco.raise_window()
                                    win.raise_window()
                                    active_window = win
                                    #
                                    self.refresh_title(win, deco)
                            #
                            continue
                        #
                        # the programs
                        self.mouse_button_left = 1
                        # event.child is the decoration
                        geom = event.child.get_geometry()
                        cx = geom.x
                        cy = geom.y
                        x = event.root_x
                        y = event.root_y
                        self.delta_drag_start_point = (x - cx, y - cy)
                        #
                        # close button
                        if cx+geom.width-8-BUTTON_SIZE < x < cx+geom.width-8 and cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1) < y < cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1)+BUTTON_SIZE:
                            self.close_btn_pressed = 1
                        # maximize button
                        elif cx+geom.width-BUTTON_SIZE*2-10 < x < cx+geom.width-8 and cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1) < y < cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1)+BUTTON_SIZE:
                            self.maxi_btn_pressed = 1
                        #### resize window
                        # right bottom
                        if cx+geom.width-8 < x < cx+geom.width and cy+geom.height-8 < y < cy+geom.height:
                            self.mouse_button_resize_window = 1
                            self.mouse_button_resize_drag_start_point = (x, y)
                            self.window_resize_geometry = (geom.x, geom.y, geom.width, geom.height)
                            root_cursor_right_corner_bottom()
                        #
                        event.child.grab_pointer(
                                True, X.PointerMotionMask | X.ButtonReleaseMask, X.GrabModeAsync,
                                X.GrabModeAsync, X.NONE, X.NONE, 0)
                        # 
                        # find and set the active window
                        if active_window:
                            if active_window in DECO_WIN:
                                if DECO_WIN[active_window] == event.child:
                                    pass
                                else:
                                    win = self.find_win_of_deco(event.child)
                                    if win:
                                        event.child.raise_window()
                                        win.raise_window()
                                        event.child.change_attributes(event_mask=X.NoEventMask)
                                        active_window = win
                                        active_deco = DECO_WIN[win]
                                        active_deco.change_attributes(event_mask=mask_deco)
                                        # refresh the title
                                        self.refresh_title(win, event.child)
                                        # 
                                        all_windows_stack.remove(win)
                                        all_windows_stack.append(win)
                        else:
                            win = self.find_win_of_deco(event.child)
                            if win:
                                event.child.raise_window()
                                win.raise_window()
                                self.refresh_title(win, event.child)
                                active_window = win
                    
                    else:
                        # on root
                        pass
                #
                # right button
                elif event.detail == 3:
                    if event.child == 0:
                        self._menu(event.root_x, event.root_y)
                    else:
                        #
                        if event.child == self._dock:
                            geom = event.child.get_geometry()
                            py = event.root_y
                            # the items in the dock - minimize or restore
                            if py > dock_height:
                                n_item = int((event.root_y-dock_height)/50)
                                #
                                win = None
                                for k,v in self.dock_items.items():
                                    if v[1] == n_item:
                                        win = k
                                        break
                                #
                                v = self.dock_items[win]
                                # minimize
                                if v[0] == 0:
                                    win.unmap()
                                    DECO_WIN[win].unmap()
                                    self.dock_items[win] = [1, v[1]]
                                    self.on_dock_items_f(None, self.dock_items)
                                # restore
                                else:
                                    deco = DECO_WIN[win]
                                    deco.map()
                                    win.map()
                                    deco.raise_window()
                                    win.raise_window()
                                    self.dock_items[win] = [0, v[1]]
                                    self.on_dock_items_f(None, self.dock_items)
                                    #
                                    self.refresh_title(win, deco)
                                    #
                                    active_window = win
                            # the dock
                            else:
                                self._dock.raise_window()
                                active_window = None
            
            #
            elif event.type == X.ButtonRelease:
                if event.detail == 1:
                    self.window_button1_grab = None
                    self.mouse_button_left = 0
                    self.delta_drag_start_point = None
                    #
                    if event.child == self._dock:
                        continue
                    # 
                    elif event.child != 0:
                        geom = event.child.get_geometry()
                        cx = geom.x
                        cy = geom.y
                        x = event.root_x
                        y = event.root_y
                        # 
                        # close button
                        if self.close_btn_pressed:
                            win = self.find_win_of_deco(event.child)
                            self.close_window(win)
                        # maximize button
                        elif self.maxi_btn_pressed:
                            self.window_maximized = 1
                            self.maximize_window(event.child)
                        #
                        # elif cx+geom.width-BUTTON_SIZE*3-10 < x < cx+geom.width-8 and cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1) < y < cy+int((TITLE_HEIGHT-BUTTON_SIZE)/2+1)+BUTTON_SIZE:
                            # pass
                    #
                    if self.mouse_button_resize_window:
                        root_cursor_normal()
                        self.mouse_button_resize_window = 0
                        self.mouse_button_resize_drag_start_point = None
                        self.window_resize_geometry = None
                        self.window_maximized = 0
                    #
                    self.display.ungrab_pointer(X.CurrentTime)
                    #
                    self.close_btn_pressed = 0
                    self.maxi_btn_pressed = 0
                # right button
                elif event.detail == 3:
                    if self._m:
                        if event.child == self._m:
                            geom = event.child.get_geometry()
                            if geom.x<event.root_x<(geom.x+geom.width) and geom.y<event.root_y<(geom.y+50):
                                self.prog_execute("xterm")
                            elif geom.x<event.root_x<(geom.x+geom.width) and (geom.y+50)<event.root_y<(geom.y+100):
                                self.prog_exit()
                        #
                        self._m.destroy()
                        self._m = None
            
            #
            elif event.type == X.KeyPress:
                if event.detail == ALT_KEY:
                    if self._is_alt:
                        if active_window:
                            if event.child == active_window:
                                _can_drag = 1
                                def _on_error(data):
                                    _can_drag = 0
                                # event.child.change_attributes(event_mask=X.PointerMotionMask | X.ButtonPressMask | X.ButtonReleaseMask)
                                event.child.change_attributes(event_mask=X.PointerMotionMask)
                                event.child.grab_button(1, X.AnyModifier, True,
                                    X.ButtonPressMask, X.GrabModeAsync,
                                    X.GrabModeAsync, X.NONE, X.NONE, onerror=_on_error)
                                if _can_drag:
                                    # event.child is the program
                                    self.window_button1_grab = event.child
                                    self.mouse_button_left = 1
                # screen shot
                elif event.detail == STAMP_KEY:
                    if _SCREENSHOT:
                        take_screenshot(0,0,screen_width,screen_height)
                # bring the dock to top
                elif event.detail == self.display.keysym_to_keycode(XK.string_to_keysym(DOCK_KEY)):
                    keycode = event.detail
                    keysym = self.display.keycode_to_keysym(keycode, 0)
                    char = XK.keysym_to_string(keysym)
                    if char == DOCK_KEY and _create_dock:
                        self._dock.raise_window()
                        active_window = None
                # # bring up the menu
                # elif event.detail == self.display.keysym_to_keycode(XK.string_to_keysym(MENU_KEY)):
                    # keycode = event.detail
                    # keysym = self.display.keycode_to_keysym(keycode, 0)
                    # char = XK.keysym_to_string(keysym)
                
            #
            elif event.type == X.KeyRelease:
                if event.detail == ALT_KEY:
                    if self.window_button1_grab:
                        if event.child == self.window_button1_grab:
                            self.window_button1_grab.ungrab_button(1, X.AnyModifier)
                            self.window_button1_grab = None
                            self.mouse_button_left = 0
            
            #
            if not _is_running:
                break
        else:
            print("exiting from loop...")
    

    def prog_exit(self):
        global _is_running
        _is_running = 0
        sys.exit(0)
        
    

##############

x_wm()
    
    