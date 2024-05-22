from  tkinter import ttk
from tkinter import StringVar
from window_control import *
from universal import *

class handle_cbbox():
    # 输入：所在框架、坐标、长度
    def __init__(s,frm,x,y,width):
        s.frm=frm
        s.list=[]
        s.cv=StringVar()
        s.send_result_handle=False
        s.box=ttk.Combobox(frm,textvariable=s.cv,width=width)
        s.box.place(x=x,y=y)
        s.box.bind("<<ComboboxSelected>>",s.selecthwnd)
        
    def get_all_handel_name(s):
        value=getallhwndname()
        s.box['value']=value
        s.list=[i for i in value]
        s.setfirst()
        
    def setfirst(self):
        if len(self.box['value']):
            self.cv.set(self.list[0])


    def selecthwnd(self,*event):
        self.send_result_handle=self.cv.get()
        print(self.send_result_handle)
        if self.send_result_handle=='':
            self.send_result_handle=False
            


