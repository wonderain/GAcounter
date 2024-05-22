import os.path
import time
from ELO import *
from Player_Database import *
from img_deal import *
from Handle_Combobox import *
from Combobox import *
from universal import *
from window_control import *
import datetime
import tkinter as tk
import atexit
from io import BytesIO



# 判断是什么界面
def which_screen(max_time=5,delay=0.5):
    color_points_value_list=get_global('color_points_value_list')
    color_points_name_list=get_global('color_points_name_list')
    sysexit = get_global('sysexit')
    for i in range(max_time):
        if sysexit:
            return False
        img=fetch_image('新热血英豪')
        for points_name in ['在大厅中','在游戏中',"在房间中","回合得分","当前得分","颁奖典礼","最终结果"]:
            pl=color_points_value_list[color_points_name_list.index(points_name)]
            cl = color_points_value_list[color_points_name_list.index(points_name + '_rgb')]
            point_list = [pl[i:i + 2] for i in range(0, len(pl), 2)]
            color_list = [cl[i:i + 3] for i in range(0, len(cl), 3)]
            result=pic_match(img, point_list, color_list, 5)
            if result:
                return points_name
        time.sleep(delay)
        sysexit = get_global('sysexit')

print(which_screen())
input()
