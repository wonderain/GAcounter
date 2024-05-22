from ELO import *
import tkinter as tk
from Combobox import *
import threading

#简单地将函数打包进线程
def threadit(func, *args):
    # 创建
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    # 启动
    t.start()


def input_elo_data_thread():
    threadit(input_elo_data)

def input_elo_data():
    # 处理新来源分类
    match_path=choose_match.getvalue()
    root_path=path_entry.get()
    path_entry.delete(0, tk.END)
    if root_path=='' or not os.path.exists(root_path):
        print('目录错误')
        return False
    btn['state']=tk.DISABLED
    source_list=[i for i in os.listdir(root_path) if os.path.isdir(root_path+'/'+i)]
    elo_json_in_which_source_dict={}   #储存elo数据的名字（时间）以及其来源
    for source in source_list:
        for elo_json in os.listdir('%s/%s/elo_uninput_data'%(root_path,source)):
            elo_json_in_which_source_dict[elo_json]=source
    for k,v in elo_json_in_which_source_dict.items():
        print(k,v)

    # 将新源临时玩家数据库移入总数据库并建立对应，注意No都是字符格式
    if os.path.exists(root_path+'/source_tempNo_No_dict.json'):
        source_tempNo_No_dict=json_read(root_path+'/source_tempNo_No_dict.json')
    else:
        source_tempNo_No_dict={}
        for source in source_list:
            source_tempNo_No_dict[source]={}
            for temp_No_imgpath in os.listdir('%s/%s/player_database'%(root_path,source)):
                # 如果是图片
                if '.png' in temp_No_imgpath:
                    temp_No=temp_No_imgpath.replace('.png','')
                    img=Image.open('%s/%s/player_database/%s'%(root_path,source,temp_No_imgpath))
                    search_result=player_database().which_player_in_database(img)['No']
                    source_tempNo_No_dict[source][temp_No]=search_result
        json_write(root_path+'/source_tempNo_No_dict.json',source_tempNo_No_dict)
    for k,v in source_tempNo_No_dict.items():
        print(k,v )
    # 按顺序排列所有elo_json，取时间在前的先计算
    elo_json_sort_list=sorted(elo_json_in_which_source_dict.keys(),reverse=False)
    for elo_json in elo_json_sort_list:
        source=elo_json_in_which_source_dict[elo_json]
        # 提取数据
        elo_info=json_read('%s/%s/elo_uninput_data/%s'%(root_path,source,elo_json))
        # 将tempNo转化为正式No
        for index,temp_No in enumerate(elo_info['team1']):
            elo_info['team1'][index]=source_tempNo_No_dict[source][str(temp_No)]
        for index,temp_No in enumerate(elo_info['team2']):
            elo_info['team2'][index]=source_tempNo_No_dict[source][str(temp_No)]
        print(str(elo_info))
        elo_open(match_path).input_new_record(elo_info)
        btn['state'] =tk.NORMAL

if not os.path.exists('match_list.json'):
    exit(1)
match_list=json_read('match_list.json')
root=tk.Tk(className='input')
root.geometry('200x60')
tk.Label(root,text='选择比赛').place(x=5,y=5)
choose_match=cbbox(root,60,5,8)
choose_match.setvalue(match_list)
tk.Label(root,text='输入根目录').place(x=5,y=35)
path_entry=tk.Entry(root,width=15)
path_entry.place(x=70,y=35)
btn=tk.Button(root,text='确定',command=input_elo_data_thread)
btn.place(x=150,y=0)
root.mainloop()