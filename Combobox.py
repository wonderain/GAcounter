from  tkinter import ttk
from tkinter import StringVar

class cbbox():
    # 输入：所在框架、坐标、长度
    def __init__(s,frm,x,y,width):
        s.frm=frm
        s.list=[]
        s.cv=StringVar()
        s.box=ttk.Combobox(frm,textvariable=s.cv,width=width)
        s.box.place(x=x,y=y)
    def setvalue(s,value):
        s.box['value']=value
        s.list=[i for i in value]
        s.setfirst()
    def setfirst(self):
        if len(self.box['value']):
            self.cv.set(self.list[0])
    def getvalue(s):
        return s.cv.get()
    def bindselect(s,function):
        s.box.bind("<<ComboboxSelected>>",function)


