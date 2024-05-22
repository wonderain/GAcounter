import time
import psutil
import pythoncom
import win32api,win32con,win32gui,win32com.client,win32print
import win32clipboard as clip
from universal import *

# 程序是否运行
def whether_process_running(process_name):
    for pid in psutil.pids():
        if psutil.Process(pid).name()==process_name:
            return True
    return False

#获取所有的窗口名称
def getallhwndname():
    titles=[]
    def foo(hwnd,mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            title=win32gui.GetWindowText(hwnd)
            if title!='':
                titles.append(win32gui.GetWindowText(hwnd))
    win32gui.EnumWindows(foo, 0)
    #print(titles)
    return titles

def setImage(data):
    clip.OpenClipboard() #打开剪贴板
    clip.EmptyClipboard()  #先清空剪贴板
    clip.SetClipboardData(win32con.CF_DIB, data)  #将图片放入剪贴板
    clip.CloseClipboard()


# 输入窗口名，返回窗口坐标矩形和句柄
def get_window_pos(window_name):
    handle=win32gui.FindWindow(0,window_name)
    if handle==0:
        printlog('游戏未打开')
        return False,False
    else:
        rect=win32gui.GetWindowRect(handle)
        settings=get_global('settings')
        gf=settings['全局截图偏移']
        #print(gf)
        return (rect[0]+gf[0],rect[1]+gf[1],rect[2]+gf[2],rect[3]+gf[3]),handle

# 输入窗口名截图
def fetch_image(window_name):
    try:
        pos,handle=get_window_pos(window_name)
        window_image=ImageGrab.grab(pos,all_screens=True)   #存在多个显示器需要开启all_screens
        set_global('window_image',window_image)
        return window_image
    except:
        print('未能找到游戏窗口')
        return False


# 发送字符串到窗口
def send_string_to_window(handle,string:str,click_pos:tuple=False):
    if click_pos:
        pos=win32gui.GetWindowRect(handle)
        Virtual_Keyboard(pos,handle).mouse_press(click_pos)
    for x in string:
        #print(x.encode('utf-8'), ord(x))
        win32gui.PostMessage(handle, win32con.WM_CHAR, ord(x), 0)


class Virtual_Keyboard(object):

    def __init__(self, rect,hwnd):
        self.rect=rect
        self.hwnd = hwnd
        self.hwnd_title = win32gui.GetWindowText(hwnd)
        self.vlaue_key = {
            'ENTER':[13,win32con.VK_RETURN],
            'BACKSPACE':[8,win32con.VK_BACK],
            "A": [65,None],
            "B": [66,None],
            "C": [67,None],
            "D": [68,None],
            "E": [69,None],
            "F": [70,None],
            "G": [71,None],
            "H": [72,None],
            "I": [73,None],
            "J": [74,None],
            "K": [75,None],
            "L": [76,None],
            "M": [77,None],
            "N": [78,None],
            "O": [79,None],
            "P": [80,None],
            "Q": [81,None],
            "R": [82,None],
            "S": [83,None],
            "T": [84,None],
            "U": [85,None],
            "V": [86,None],
            "W": [87,None],
            "X": [88,None],
            "Y": [89,None],
            "Z": [90,None],
            "0": [48,win32con.VK_NUMPAD0],
            "1": [49,win32con.VK_NUMPAD1],
            "2": [50,win32con.VK_NUMPAD2],
            "3": [51,win32con.VK_NUMPAD3],
            "4": [52,win32con.VK_NUMPAD4],
            "5": [53,win32con.VK_NUMPAD5],
            "6": [54,win32con.VK_NUMPAD6],
            "7": [55,win32con.VK_NUMPAD7],
            "8": [56,win32con.VK_NUMPAD8],
            "9": [57,win32con.VK_NUMPAD9],
            "F1": [112,win32con.VK_F1],
            "F2": [113,win32con.VK_F2],
            "F3": [114,win32con.VK_F3],
            "F4": [115,win32con.VK_F4],
            "F5": [116,win32con.VK_F5],
            "F6": [117,win32con.VK_F6],
            "F7": [118,win32con.VK_F7],
            "F8": [119,win32con.VK_F8],
            "F9": [120,win32con.VK_F9],
            "F10":[121,win32con.VK_F10],
            "F11": [122,win32con.VK_F11],
            "F12": [123,win32con.VK_F12],
            "TAB": [9,win32con.VK_TAB],
            "ALT": [18,win32con.VK_MENU],
            'CTRL':[17,win32con.VK_LCONTROL],
            'SHIFT':[16,win32con.VK_LSHIFT],
            'ESC':[27,win32con.VK_ESCAPE],
            'PAGEUP':[33,win32con.VK_PRIOR],
            'PAGEDOWN': [34, win32con.VK_NEXT]
        }


    # 模拟一次按键的输入，间隔值默认0.1S
    def key_press(self, key: str, interval=0.2):
        key = key.upper()
        key_num = self.vlaue_key[key][0]
        num = win32api.MapVirtualKey(key_num, 0)
        dparam = 1 | (num << 16)
        uparam = 1 | (num << 16) | (1 << 30) | (1 << 31)
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, self.vlaue_key[key][1], dparam)
        time.sleep(interval)
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, self.vlaue_key[key][1], uparam)
        print('press:',key)

    # 第二种模拟按键的方法
    def key_press2(self,key:str,interval=0.2):
        current_window = win32gui.GetForegroundWindow()
        if current_window!='新热血英豪':
            pythoncom.CoInitialize()
            win32com.client.Dispatch('WScript.Shell').SendKeys('%')
            win32gui.SetForegroundWindow(self.hwnd)
        key_num = int(self.vlaue_key[key][0])
        win32api.keybd_event(key_num, 0, 0, 0)
        time.sleep(interval)
        win32api.keybd_event(key_num, 0, win32con.KEYEVENTF_KEYUP, 0)
        #print('key:',key)
        if current_window != '新热血英豪':
            win32gui.SetForegroundWindow(current_window)
            pythoncom.CoUninitialize()

    # 模拟一个按键的按下
    def key_down(self, key: str):
        key = key.upper()
        key_num = self.vlaue_key[key][0]
        num1 = win32api.MapVirtualKey(key_num, 0)
        dparam = 1 | (num1 << 16)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, self.vlaue_key[key][1], dparam)

    # 模拟一个按键的弹起
    def key_up(self, key: str):
        key = key.upper()
        key_num = self.vlaue_key[key][0]
        num1 = win32api.MapVirtualKey(key_num, 0)
        uparam = 1 | (num1 << 16) | (1 << 30) | (1 << 31)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, self.vlaue_key[key][1], uparam)

    # 模拟鼠标的移动（显示器）
    def mouse_move(self, x, y):
        x = x+self.rect[0]
        y = y+self.rect[1]
        win32api.SetCursorPos((x, y))

    # 模拟鼠标的移动后回到原位（显示器）
    def mouse_move_and_back(self,x,y,delay=0.5):
        current_window = win32gui.GetForegroundWindow()
        pythoncom.CoInitialize()
        win32com.client.Dispatch('WScript.Shell').SendKeys('%')
        win32gui.SetForegroundWindow(self.hwnd)
        last_pos=win32api.GetCursorPos()
        #print(last_pos)
        x = int(x+ self.rect[0])
        y = int(y+ self.rect[1])
        win32api.SetCursorPos((x, y))
        time.sleep(delay)
        win32api.SetCursorPos(last_pos)
        #print(current_window)
        try:
            win32gui.SetForegroundWindow(current_window)
        except:
            pass
        pythoncom.CoUninitialize()


    # 模拟鼠标的按键抬起
    def mouse_up(self, x, y, button="L"):
        x = int(x)
        y = int(y)
        button = button.upper()
        point = win32api.MAKELONG(x, y)
        if button == "L":
            win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)
        elif button == "R":
            win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON, point)

    # 模拟鼠标的按键按下
    def mouse_down(self, x, y, button="L"):
        x = int(x)
        y = int(y)
        button = button.lower()
        point = win32api.MAKELONG(x, y)
        if button == "L":
            win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        elif button == "R":
            win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, point)

    # 模拟鼠标的左键双击
    def mouse_double(self, x, y):
        x = int(x)
        y = int(y)
        point = win32api.MAKELONG(x, y)
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, point)
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)

    # 模拟鼠标左键单击（其中y-30是减去窗口标题栏）,normal指归正位置(0，0)
    def mouse_press(self, x, y,move=False,interval=0.2,normal=False):
        if normal:
            win32api.SetCursorPos((self.rect[0], self.rect[1]))
        if move:
            win32api.SetCursorPos((x+self.rect[0], y+self.rect[1]))
        point = win32api.MAKELONG(x, y-30)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        time.sleep(interval)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)
        if normal:
            win32api.SetCursorPos((self.rect[0], self.rect[1]))

    # 模拟鼠标中键单击
    def mouse_middle_press(self,x,y,interval=0.2):
        current_window = win32gui.GetForegroundWindow()
        pythoncom.CoInitialize()
        win32com.client.Dispatch('WScript.Shell').SendKeys('%')
        #win32gui.SetForegroundWindow(self.hwnd)
        last_pos = win32api.GetCursorPos()
        # print(last_pos)
        x = int(x + self.rect[0])
        y = int(y + self.rect[1])
        win32api.SetCursorPos((x, y))
        time.sleep(interval)
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
        time.sleep(0.2)
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
        win32api.SetCursorPos(last_pos)
        #print(current_window)
        win32gui.SetForegroundWindow(current_window)
        pythoncom.CoUninitialize()


    # 模拟鼠标进行左键双击
    def mouse_press_double(self, x, y):
        point = win32api.MAKELONG(x, y-30)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        time.sleep(0.1)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        time.sleep(0.1)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)



if __name__=='__main__':
    #rect, handle = get_window_pos('新热血英豪')
    while True:
        img=fetch_image('新热血英豪')
        for x in range(390,516):
            print(x,img.getpixel((390,788)))
        print('==================')
        time.sleep(0.1)
    fetch_image('新热血英豪').save('1.png')
    #Virtual_Keyboard(rect,handle).key_press('F5')
    '''
    rect,handle=get_window_pos('新热血英豪')
    window_image = ImageGrab.grab(rect, all_screens=True)
    now_weapon_img=window_image.crop((865, 372, 905, 412))
    Virtual_Keyboard(rect, handle).mouse_move_and_back(940, 355)
    '''
    '''
    num=0
    window_image = ImageGrab.grab(rect, all_screens=True)
    window_image.crop((548, 401, 588, 441)).save('weapons/%d.png' % 789)
    window_image.crop((548, 441, 588, 481)).save('weapons/%d.png' % 790)
    window_image.crop((548, 481, 588, 521)).save('weapons/%d.png' % 791)
    
    while True:
        window_image=ImageGrab.grab(rect,all_screens=True)
        window_image.crop((548,361,588,401)).save('weapons/%d.png'%num)
        Virtual_Keyboard(rect,handle).mouse_press(1045,480)
        num+=1
        time.sleep(1)'''
