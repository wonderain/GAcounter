'''本文件是用来储存全局变量的，但是要注意数据不能随便写入，只能由一个PY文件、最好带上锁来进行写入'''
import traceback
import time
import os

# 输出错误日志，分为三个等级，error严重-1级、warning警告-2、message提示-3
def log_e(msg,level:int=1):
    level_=['严重 ','警告 ','提示 '][level-1]
    try:
        os.mkdir('data/log')
    except:
        pass
    with open('data/log/log%s.txt' % time.strftime("%Y-%m-%d", time.localtime()), 'a', encoding='utf-8') as f:
        f.write(level_+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+'\n')
        f.write(msg)
        f.write('=====================================\n')


def inter_global_init():
    """
    全局变量初始化，在universal使用一次
    """
    global _global_dict
    _global_dict = {}

def set_global(key, value):
    global _global_dict
    #定义一个全局变量
    try:
        _global_dict[key] = value
    except:
        log_e(traceback.format_exc(),2)
        print('写入'+key+'失败\r\n')

def get_global(key):
    global _global_dict
    #获得一个全局变量，不存在则提示读取对应变量失败
    try:
        return _global_dict[key]
    except:
        log_e(traceback.format_exc(),2)
        print('读取'+key+'失败\r\n')

def print_all_global():
    global _global_dict
    for k,v in _global_dict.items():
        print(k)

def whether_global_exists(global_name):
    """
    查询全局变量是否存在
    :param global_name:全局变量名
    :return:是否
    """
    if global_name in _global_dict:
        return True
    return False


#这里放一下用过的所有全局变量，方便复制
'''
    settings=get_global('settings')
    infomation_before_window=get_global('infomation_before_window')                        设定在窗口创建前的信息记录
    sight_set=get_global('sight_set')
    color_points_value_list=get_global('color_points_value_list')
    color_points_name_list=get_global('color_points_name_list')
    
'''