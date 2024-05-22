import threading
from global_var import *
from PIL import Image,ImageGrab,ImageTk
import time
import os
import sys
import traceback
import json
import datetime
import shutil

inter_global_init()
set_global('log', '')

def makedir(dir):
    try:
        os.mkdir(dir)
    except:
        pass

# print+文本记录
def printlog(*text,end='\n'):
    """
    print+log文本记录，数据中存在超全局变量中
    :param text:
    :param end:
    """
    log=get_global('log')
    for t in text:
        print(t,end=' ')
        log+=str(t)
    log+='\n'
    set_global('log',log)
    print()


def json_read(path:str):
    if not os.path.exists(path):
        return False
    with open(path, 'r',encoding='utf-8') as f:
        result=json.loads(f.read())
    return result

def json_write(path:str,data,indent=4):
    with open(path, 'w',encoding='utf-8') as f:
        if indent:
            f.write(json.dumps(data,indent=indent,ensure_ascii=False))
        else:# 通过replace增加可读性
            f.write(json.dumps(data, ensure_ascii=False).replace(', "',',\n "').replace('{','{\n').replace('}','\n}'))
    return True



def get_datetime():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# 时间消耗装饰器
def cost_time(func):
    def core():
        start=time()
        func()
        print('运行函数%s一次花费%d秒'%(time()-start,func.__name__))
    return core


def get_settings():
    if not os.path.exists('main_settings.json'):
        sys.exit(0)
        return False
    settings=json_read('main_settings.json')
    return settings
settings=get_settings()
# 提取设置中的特别数据，避免放入global之后无法hash化list的问题
color_points_name_list=[]
color_points_value_list=[]
for name,value in settings['color_points'].items():
    color_points_name_list.append(name)
    color_points_value_list.append(value)
set_global('color_points_value_list',color_points_value_list)   # 变量名
set_global('color_points_name_list',color_points_name_list)     # 变量值
set_global('settings',settings)
set_global('sysexit',False)





#简单地将函数打包进线程
def threadit(func, *args):
    # 创建
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    # 启动
    t.start()


# 字典按值排序并给出排名序号(从大到小)
def value_down_sort(d:dict):
    value_list=list(set([v for v in d.values()]))
    value_list.sort(reverse=True)
    result={}
    order=1
    for i in value_list:
        order_count=0
        for k,v in d.items():
            if v==i:
                result[k]=order
                order_count+=1
        order+=order_count
    return result
# 返回列表最大值的位置
def which_max(l):
    """
    返回列表最大值的位置
    :param l: 列表
    :return:最大值的索引
    """
    m=max(l)
    re=[]
    for index,i in enumerate(l):
        if i==m:
            re.append(index)
    return re

# name_list,v1_list,v2_list按照对应放置，双值排序
def double_sort(name_list_,v1_list_,v2_list_):
    if len(name_list_)!=len(v1_list_) or len(name_list_)!=len(v2_list_):
        print('排序列表未对应')
        return False
    name_list=[i for i in name_list_]
    v1_list=[i for i in v1_list_]
    v2_list=[i for i in v2_list_]
    result={}
    order=0
    while len(name_list):
        v1_max=which_max(v1_list)
        if len(v1_max)>1:
            v2_max=which_max([v2_list[i] for i in v1_max])
            if len(v2_max)>1:
                max_indexs=[]
                for j in v2_max:
                    max_index=v1_max[j]
                    max_indexs.append(max_index)
                    result[name_list[max_index]]=order
                    order+=1
                max_indexs.sort(reverse=True)
                for j in max_indexs:
                    del name_list[j]
                    del v1_list[j]
                    del v2_list[j]
            else:
                max_index=v1_max[v2_max[0]]
                result[name_list[max_index]]=order
                del name_list[max_index]
                del v1_list[max_index]
                del v2_list[max_index]
                order+=1
        else:
            max_index=v1_max[0]
            result[name_list[max_index]]=order
            del name_list[max_index]
            del v1_list[max_index]
            del v2_list[max_index]
            order+=1
    return result
        
    
if __name__ =='__main__':
    l={'a':1,'b':2,'c':3,'d':2}
    print(str(value_down_sort(l)))
    l1=['a','b','c','d','e']
    l2=[5,2,5,7,5]
    l3=[123,234,456,1,123]
    print(str(double_sort(l1,l2,l3)))
    l={'a':[[1],[2]],'b':[2,3],'c':[3,4],'d':[4,5]}
    a='a'
    settings=json_read('main_settings.json')
    a= '红方失败'
    print(settings['color_points'][a])