#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   AutoClick.py
@Time    :   2021/10/09 15:10:01
@Author  :   Yaadon 
'''

# here put the import lib
import win32con
import win32gui
import win32ui
import time
import numpy as np
import os
from PIL import Image
import aircv as ac
from ctypes import windll, byref
from ctypes.wintypes import HWND, POINT
import string
# import sys
# import cv2
# from memory_pic import *
# import win32api
# import autopy
# from PIL import ImageGrab

scale = 1 # 电脑的缩放比例
# scale = 1.25 # 电脑的缩放比例
radius = 5 # 随机半径
x_coor = 10 # 窗口位置
y_coor = 10 # 窗口位置

class AutoClick():
    """
    @description  :自动点击类，包含后台截图、图像匹配
    ---------
    @param  :
    -------
    @Returns  :
    -------
    """
    
    __PostMessageW = windll.user32.PostMessageW
    __SendMessageW = windll.user32.SendMessageW
    __MapVirtualKeyW = windll.user32.MapVirtualKeyW
    __VkKeyScanA = windll.user32.VkKeyScanA
    __ClientToScreen = windll.user32.ClientToScreen

    __WM_KEYDOWN = 0x100
    __WM_KEYUP = 0x101
    __WM_MOUSEMOVE = 0x0200
    __WM_LBUTTONDOWN = 0x0201
    __WM_LBUTTONUP = 0x202
    __WM_RBUTTONDOWN = 0x0204
    __WM_RBUTTONUP = 0x205
    __WM_MOUSEWHEEL = 0x020A
    __WHEEL_DELTA = 120
    __WM_SETCURSOR = 0x20
    __WM_MOUSEACTIVATE = 0x21

    __HTCLIENT = 1
    __MA_ACTIVATE = 1

    __VkCode = {
        "back":  0x08,
        "tab":  0x09,
        "return":  0x0D,
        "shift":  0x10,
        "control":  0x11,
        "menu":  0x12,
        "pause":  0x13,
        "capital":  0x14,
        "escape":  0x1B,
        "space":  0x20,
        "end":  0x23,
        "home":  0x24,
        "left":  0x25,
        "up":  0x26,
        "right":  0x27,
        "down":  0x28,
        "print":  0x2A,
        "snapshot":  0x2C,
        "insert":  0x2D,
        "delete":  0x2E,
        "lwin":  0x5B,
        "rwin":  0x5C,
        "numpad0":  0x60,
        "numpad1":  0x61,
        "numpad2":  0x62,
        "numpad3":  0x63,
        "numpad4":  0x64,
        "numpad5":  0x65,
        "numpad6":  0x66,
        "numpad7":  0x67,
        "numpad8":  0x68,
        "numpad9":  0x69,
        "multiply":  0x6A,
        "add":  0x6B,
        "separator":  0x6C,
        "subtract":  0x6D,
        "decimal":  0x6E,
        "divide":  0x6F,
        "f1":  0x70,
        "f2":  0x71,
        "f3":  0x72,
        "f4":  0x73,
        "f5":  0x74,
        "f6":  0x75,
        "f7":  0x76,
        "f8":  0x77,
        "f9":  0x78,
        "f10":  0x79,
        "f11":  0x7A,
        "f12":  0x7B,
        "numlock":  0x90,
        "scroll":  0x91,
        "lshift":  0xA0,
        "rshift":  0xA1,
        "lcontrol":  0xA2,
        "rcontrol":  0xA3,
        "lmenu":  0xA4,
        "rmenu":  0XA5
    }

    def __get_virtual_keycode(self, key: str):
        """根据按键名获取虚拟按键码

        Args:
            key (str): 按键名

        Returns:
            int: 虚拟按键码
        """
        if len(key) == 1 and key in string.printable:
            # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscana
            return self.__VkKeyScanA(ord(key)) & 0xff
        else:
            return self.__VkCode[key]


    def __key_down(self, handle: HWND, key: str):
        """按下指定按键

        Args:
            handle (HWND): 窗口句柄
            key (str): 按键名
        """
        vk_code = self.__get_virtual_keycode(key)
        scan_code = self.__MapVirtualKeyW(vk_code, 0)
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keydown
        wparam = vk_code
        lparam = (scan_code << 16) | 1
        self.__PostMessageW(handle, self.__WM_KEYDOWN, wparam, lparam)


    def __key_up(self, handle: HWND, key: str):
        """放开指定按键

        Args:
            handle (HWND): 窗口句柄
            key (str): 按键名
        """
        vk_code = self.__get_virtual_keycode(key)
        scan_code = self.__MapVirtualKeyW(vk_code, 0)
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keyup
        wparam = vk_code
        lparam = (scan_code << 16) | 0XC0000001
        self.__PostMessageW(handle, self.__WM_KEYUP, wparam, lparam)


    def __activate_mouse(self, handle: HWND):
        """
        @Description : 激活窗口接受鼠标消息
        ---------
        @Args : handle (HWND): 窗口句柄
        -------
        @Returns : 
        -------
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-mouseactivate
        lparam = (self.__WM_LBUTTONDOWN << 16) | self.__HTCLIENT
        self.__SendMessageW(handle, self.__WM_MOUSEACTIVATE, self.__handle, lparam)
    

    def __set_cursor(self, handle: HWND, msg):
        """
        @Description : Sent to a window if the mouse causes the cursor to move within a window and mouse input is not captured
        ---------
        @Args : handle (HWND): 窗口句柄, msg : setcursor消息
        -------
        @Returns : 
        -------
        """
        # https://docs.microsoft.com/en-us/windows/win32/menurc/wm-setcursor
        lparam = (msg << 16) | self.__HTCLIENT
        self.__SendMessageW(handle, self.__WM_SETCURSOR, handle, lparam)

    
    def __move_to(self, handle: HWND, x: int, y: int):
        """移动鼠标到坐标（x, y)

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-mousemove
        wparam = 0
        lparam = y << 16 | x
        self.__PostMessageW(handle, self.__WM_MOUSEMOVE, wparam, lparam)


    def __left_down(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)按下鼠标左键

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-lbuttondown
        wparam = 0x001
        lparam = y << 16 | x
        self.__PostMessageW(handle, self.__WM_LBUTTONDOWN, wparam, lparam)


    def __left_up(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)放开鼠标左键

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-lbuttonup
        wparam = 0
        lparam = y << 16 | x
        self.__PostMessageW(handle, self.__WM_LBUTTONUP, wparam, lparam)

    def __right_down(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)按下鼠标右键

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-lbuttondown
        wparam = 0x001
        lparam = y << 16 | x
        self.__PostMessageW(handle, self.__WM_RBUTTONDOWN, wparam, lparam)

    def __right_up(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)放开鼠标又键

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-lbuttonup
        wparam = 0
        lparam = y << 16 | x
        self.__PostMessageW(handle, self.__WM_RBUTTONUP, wparam, lparam)

    def __scroll(self, handle: HWND, delta: int, x: int, y: int):
        """在坐标(x, y)滚动鼠标滚轮

        Args:
            handle (HWND): 窗口句柄
            delta (int): 为正向上滚动，为负向下滚动
            x (int): 横坐标
            y (int): 纵坐标
        """
        self.__move_to(handle, x, y)
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-mousewheel
        wparam = delta << 16
        p = POINT(x, y)
        self.__ClientToScreen(handle, byref(p))
        lparam = p.y << 16 | p.x
        self.__PostMessageW(handle, self.__WM_MOUSEWHEEL, wparam, lparam)


    def __scroll_up(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)向上滚动鼠标滚轮

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        self.__scroll(handle, self.__WHEEL_DELTA, x, y)


    def __scroll_down(self, handle: HWND, x: int, y: int):
        """在坐标(x, y)向下滚动鼠标滚轮

        Args:
            handle (HWND): 窗口句柄
            x (int): 横坐标
            y (int): 纵坐标
        """
        self.__scroll(handle, -self.__WHEEL_DELTA, x, y)


    def get_winds(self, title: str):
        """
        @description : 获取游戏句柄 ,并把游戏窗口置顶并激活窗口
        ---------
        @param : 窗口名
        -------
        @Returns : 窗口句柄
        -------
        """
        # self.__handle = win32gui.FindWindowEx(0, 0, "Qt5QWindowIcon", "MuMu模拟器")
        self.__handle = windll.user32.FindWindowW(None, title)
        self.__classname = win32gui.GetClassName(self.__handle)
        # print(self.__classname)
        if self.__classname == 'Qt5QWindowIcon':
            self.__mainhandle = win32gui.FindWindowEx(self.__handle, 0, "Qt5QWindowIcon", "MainWindowWindow")
            # print(self.__mainhandle)
            self.__centerhandle = win32gui.FindWindowEx(self.__mainhandle, 0, "Qt5QWindowIcon", "CenterWidgetWindow")
            # print(self.__centerhandle)
            self.__renderhandle = win32gui.FindWindowEx(self.__centerhandle, 0, "Qt5QWindowIcon", "RenderWindowWindow")
            # print(self.__renderhandle)
            self.__clickhandle = self.__renderhandle
        else:
            # self.__clickhandle = self.__handle
            self.__clickhandle = 68546
        # self.__subhandle = win32gui.FindWindowEx(self.__renderhandle, 0, "subWin", "sub")
        # print(self.__subhandle)
        # self.__subsubhandle = win32gui.FindWindowEx(self.__subhandle, 0, "subWin", "sub")
        # print(self.__subsubhandle)
        # win32gui.ShowWindow(hwnd1, win32con.SW_RESTORE)
        # print(win32gui.GetWindowRect(hwnd1))
        win32gui.SetWindowPos(self.__handle, win32con.HWND_TOP, x_coor, y_coor, 0, 0, win32con.SWP_SHOWWINDOW | win32con.SWP_NOSIZE)
        print(self.__clickhandle)
        return self.__handle
    

    def get_src(self):
        """
        @description : 获得后台窗口截图
        ---------
        @param : None
        -------
        @Returns : None
        -------
        """

        left, top, right, bot = win32gui.GetWindowRect(self.__handle)
        #Remove border around window (8 pixels on each side)
        bl = 8
        #Remove border on top
        bt = 39

        width = int((right - left + 1) * scale) - 2 * bl
        height = int((bot - top + 1) * scale) - bt - bl
        # 返回句柄窗口的设备环境，覆盖整个窗口，包括非客户区，标题栏，菜单，边框
        hWndDC = win32gui.GetWindowDC(self.__handle)
        # 创建设备描述表
        mfcDC = win32ui.CreateDCFromHandle(hWndDC)
        # 创建内存设备描述表
        saveDC = mfcDC.CreateCompatibleDC()
        # 创建位图对象准备保存图片
        saveBitMap = win32ui.CreateBitmap()
        # 为bitmap开辟存储空间
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        # 将截图保存到saveBitMap中
        saveDC.SelectObject(saveBitMap)
        # 保存bitmap到内存设备描述表
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (bl, bt), win32con.SRCCOPY)
        ###获取位图信息
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        ###生成图像
        im_PIL = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        # 内存释放
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.__handle, hWndDC)
        ###PrintWindow成功,保存到文件,显示到屏幕
        # im_PIL.save("src.jpg")  # 保存
        im_PIL.show()  # 显示
    

    
    

    def recognize(self, objs):
        """
        @description : 图像识别之模板匹配
        ---------
        @param : 需要匹配的模板名
        -------
        @Returns : 将传进来的图片和全屏截图匹配如果找到就返回图像在屏幕的坐标 否则返回None
        -------
        """
        
        imobj = ac.imread(objs)
        imsrc = ac.imread('%s\\src.jpg' % os.getcwd())
        pos = ac.find_template(imsrc, imobj, 0.5)
        return pos


    def mouse_click(self, x, y, times=0.5):
        """
        @description : 单击左键
        ---------
        @param : 位置坐标x,y 单击后延时times(s)
        -------
        @Returns : 
        -------
        """
        # self.__set_cursor(self.__clickhandle, self.__WM_MOUSEACTIVATE)
        # self.__move_to(self.__clickhandle, int(x / scale), int(y / scale))
        # self.__activate_mouse(self.__clickhandle)
        # self.__set_cursor(self.__clickhandle, self.__WM_LBUTTONDOWN)
        self.__left_down(self.__clickhandle, int(x / scale), int(y / scale))
        # self.__right_down(self.__clickhandle, int(x / scale), int(y / scale))
        self.__move_to(self.__clickhandle, int(x / scale), int(y / scale))
        self.__left_up(self.__clickhandle, int(x / scale), int(y / scale))
        # self.__right_up(self.__clickhandle, int(x / scale), int(y / scale))
        time.sleep(times)
    

    def mouse_click_image(self, name : str, times = 0.5):
        """
        @Description : 鼠标左键点击识别到的图片位置
        ---------
        @Args : name:输入图片名; times:单击后延时
        -------
        @Returns : None
        -------
        """
        try:
            result = self.recognize(name)
            if result is None or result['confidence'] < 0.9:
                print("No results!")
            else:
                print(result['result'][0] + x_coor * scale + 8, " ",result['result'][1] + y_coor * scale + 39)
                self.mouse_click(result['result'][0] + x_coor * scale + 8, result['result'][1] + y_coor * scale + 39)
        except:
            raise Exception("error")

    
    def mouse_click_radius(self, x, y, times=0.5):
        """
        @description : 在范围内随机位置单击（防检测）
        ---------
        @param : 位置坐标x,y 单击后延时times(s)
        -------
        @Returns : 
        -------
        """
        
        random_x = np.random.randint(-radius, radius)
        random_y = np.random.randint(-radius, radius)
        self.mouse_click(x + random_x, y + random_y)
        # self.__left_down(self.__clickhandle, int((x + random_x) / scale), int((y + random_y) / scale))
        # time.sleep(0.1)
        # self.__left_up(self.__clickhandle, int((x + random_x) / scale), int((y + random_y) / scale))
        time.sleep(times)


    def push_key(self, key: str, times = 1):
        """
        @Description : 按键
        ---------
        @Args : key:按键 times:按下改键后距松开的延时
        -------
        @Returns : None
        -------
        """
        self.__key_down(self.__clickhandle, key)
        time.sleep(times)
        self.__key_up(self.__clickhandle, key)
        time.sleep(0.5)
    

    def type_str(self, msg: str):
        """
        @Description : 打字
        ---------
        @Args : msg:目标字符
        -------
        @Returns : None
        -------
        """
        for i in msg:
            self.__PostMessageW(self.__clickhandle, win32con.WM_CHAR, ord(i), 0)


if __name__ == '__main__':
    click = AutoClick()
    click.get_winds("微信")
    # click.get_src()
    click.mouse_click(200, 300)
    # click.mouse_click_image('test.png')
    click.mouse_click(1086, 269) # 输入框
    click.mouse_click(237, 211) # 输入框
    click.mouse_click(1228, 201) # 输入框
    click.type_str("123木头人abc")
