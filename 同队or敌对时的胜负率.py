import tkinter as tk
from PIL import Image,ImageTk,ImageDraw,ImageFont
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False
from universal import *
from scipy.stats import kstest
from Combobox import *
import numpy as np


def get_datetime():
    return datetime.datetime.now().strftime('%Y%m%d')

def json_read(path):
    with open(path,'r',encoding='utf-8')as f:
        text=json.loads(f.read())
    return text

# 用于展现每个人跟谁同队胜率最高，跟谁敌对胜率最低
def main():
    match_name = choose_match.getvalue()
    global frame
    players_info = {}
    players_No_list=[]
    players_name_list=[]
    for i in os.listdir('%s/players' % match_name):
        player_No=i[:i.rfind('.')]
        players_info[player_No] = json_read('%s/players/' % match_name + i)
        # 参赛次数少于20的不计算
        if len(players_info[player_No])<=21:
            continue
        players_No_list.append(player_No)
        name = database[str(player_No)]['name']
        players_name_list.append(name)
    if len(players_No_list)!=len(players_name_list):print(1)

    # 建立一个三维表格。第一维长度3，分别代表：同队胜利、同队失败、敌对情况：第二维name对第三维（横对竖） 表示胜利，反过来表示失败。第二维度和第三维度都是player_index
    Matrix=np.zeros((4,len(players_No_list),len(players_No_list)))
    record_info = json_read('%s/record.json' % match_name)
    for match_index,info in record_info.items():
        # 假设是第二队赢了，那么第二队成员两两增加胜利,第1队成员两两增加失败，第二队对第一队两两增加胜利，第一队对第二队两两增加失败。
        win_team=info['win']
        if win_team==0:
            continue
        lose_team=[1,2][(win_team)%2]
        win_team_member=info['team%d'%win_team]
        lose_team_member = info['team%d' % lose_team]
        for i in win_team_member:
            for j in win_team_member:
                if i!=j:
                    # 从No获取No_list中的序号,如果No不在其中会报错然后跳过
                    try:
                        i_index=players_No_list.index(str(i))
                        j_index = players_No_list.index(str(j))
                        Matrix[0,i_index,j_index]+=1
                        Matrix[0,j_index,i_index]+=1
                    except:
                        pass
        for i in lose_team_member:
            for j in lose_team_member:
                if i!=j:
                    try:
                        i_index = players_No_list.index(str(i))
                        j_index = players_No_list.index(str(j))
                        Matrix[1, i_index, j_index] += 1
                        Matrix[1, j_index, i_index] += 1
                    except:
                        pass
        for i in win_team_member:
            for j in lose_team_member:
                try:
                    i_index = players_No_list.index(str(i))
                    j_index = players_No_list.index(str(j))
                    Matrix[2, i_index, j_index] += 1
                except:
                    pass

    #print(Matrix[0,:,:])
    #print(Matrix[1, :, :])
    #print(Matrix[2, :, :])

    '''同队胜率计算'''
    # 对每个玩家，综合Matrix[0:2,,]可以得到跟同队玩家的胜率
    same_team_win_rate_Matrix=np.zeros((len(players_No_list),len(players_No_list)))
    for i in range(len(players_No_list)):
        for j in range(len(players_No_list)):
            # 对于的两个人(或一个人)一起参与少于10场，设置其胜率为-1，不纳入统计
            if (Matrix[0,i,j]+Matrix[1,i,j])<10:
                same_team_win_rate_Matrix[i, j]=-1
                same_team_win_rate_Matrix[j, i] =-1
                continue
            same_team_win_rate_Matrix[i,j]=Matrix[0,i,j]/(Matrix[0,i,j]+Matrix[1,i,j])
            same_team_win_rate_Matrix[j, i] = Matrix[0, i, j] / (Matrix[0, i, j] + Matrix[1, i, j])

    # 记录每个玩家同队胜率第一（全部用name_list中的index标记），用以计算最有默契
    same_team_win_max_rate_dict={}
    # 输出玩家同队胜率最高(3个)和最低
    for index,name in enumerate(players_name_list):
        l=same_team_win_rate_Matrix[index,:].tolist()
        same_team_win_rate_dict={}
        for i,rate in enumerate(l):
            if rate not in same_team_win_rate_dict:
                same_team_win_rate_dict[rate]=[i]
            else:
                same_team_win_rate_dict[rate].append(i)
        stwr=list(same_team_win_rate_dict.keys())
        stwr.sort(reverse=True)
        # 获取胜率列中-1的值的个数并且全部删除
        for times in   range(stwr.count(-1)):
            stwr.remove(-1)
        #print(stwr)
        text='%s  \n\t同队时胜率最高的依次为: '%name
        times=3 if len(stwr)>=3 else len(stwr)


        good_rate=[]
        for i in range(times):
            rate=stwr[i]
            for jdex in same_team_win_rate_dict[rate]:
                relative_name=players_name_list[jdex]
                if rate>0.8:
                    good_rate.append(jdex)
                # 同队次数是Matrix前两个矩阵之和
                company_times=(Matrix[0,index,jdex]+Matrix[1,index,jdex])
                if name!=relative_name:
                    text+='【%s】(%.2f,%d次) '%(relative_name,rate,company_times)
        same_team_win_max_rate_dict[index]=good_rate

        '''text+='\n\t同队时胜率最低的为: '
        lowest_rate=stwr[-1]
        for jdex in same_team_win_rate_dict[lowest_rate]:
            relative_name = players_name_list[jdex]
            # 同队次数是Matrix前两个矩阵之和
            company_times = (Matrix[0, index, jdex] + Matrix[1, index, jdex])
            if name != relative_name:
                text+='【%s】(%.2f,%d次) '%(relative_name,lowest_rate,company_times)'''
        print(text)

    # 默契组合
    '''pair_list=[]
    for index,js in same_team_win_max_rate_dict.items():
        for jndex in js:
            if jndex in same_team_win_max_rate_dict and index in same_team_win_max_rate_dict[jndex]:
                if [index,jndex] not in pair_list and [jndex,index] not in pair_list:
                    pair_list.append([index,jndex])
    for pair in pair_list:
        name1=players_name_list[pair[0]]
        name2 = players_name_list[pair[1]]
        print('%s 和 %s 可能是最佳拍档哦！'%(name1,name2))
'''

    '''敌对胜率计算'''
    diff_team_win_rate_Matrix = np.zeros((len(players_No_list), len(players_No_list)))
    for i in range(len(players_No_list)):
        for j in range(len(players_No_list)):
            # 对于的两个人(或一个人)一起参与少于10场，设置其胜率为-1，不纳入统计
            if (Matrix[2, i, j] + Matrix[2, j, i]) < 10:
                diff_team_win_rate_Matrix[i, j] = -1
                diff_team_win_rate_Matrix[j, i] = -1
                continue
            diff_team_win_rate_Matrix[i, j] = Matrix[2, i, j] / (Matrix[2, i, j] + Matrix[2, j, i])
            diff_team_win_rate_Matrix[j, i] = Matrix[2, j, i] / (Matrix[2, i, j] + Matrix[2, j, i])

    # 输出玩家敌对胜率最高(3个)和最低
    for index, name in enumerate(players_name_list):
        l = diff_team_win_rate_Matrix[index, :].tolist()
        diff_team_win_rate_dict = {}
        for i, rate in enumerate(l):
            if rate not in diff_team_win_rate_dict:
                diff_team_win_rate_dict[rate] = [i]
            else:
                diff_team_win_rate_dict[rate].append(i)
        dtwr = list(diff_team_win_rate_dict.keys())
        dtwr.sort(reverse=True)
        # 获取胜率列中-1的值的个数并且全部删除
        for times in range(dtwr.count(-1)):
            dtwr.remove(-1)
        # print(stwr)
        text = '%s  \n\t敌对时胜率最高的依次为: ' % name
        times = 3 if len(dtwr) >= 3 else len(dtwr)


        for i in range(times):
            rate = dtwr[i]
            for jdex in diff_team_win_rate_dict[rate]:
                relative_name = players_name_list[jdex]
                # 同队次数是Matrix前两个矩阵之和
                company_times = (Matrix[2, index, jdex] + Matrix[2, jdex, index])
                if name != relative_name:
                    text += '【%s】(%.2f,%d次) ' % (relative_name, rate, company_times)
        print(text)











root = tk.Tk()
w = 460
h = 400
# 记入统计的最低数量
min_count = 10
# 趋势图最低统计数量
plot_min_count = 10
# 趋势图统计最近时长
plot_recent_day = 5

# 玩家的NO.和数据库数据
database = json_read('player_database/database.json')

root.geometry("%dx%d+100+100" % (w, h))
if not os.path.exists('match_list.json'):
    tk.Label(root, text='\t\t\t未能找到比赛列表').pack()
match_list = json_read('match_list.json')
tk.Label(root, text='\tID\tNo\t等级分\t比赛次数\t平均分\t近期对手\t可信度1').pack()
choose_match = cbbox(root, 40, 2, 8)
choose_match.setvalue(match_list)
# Canvas,Scrollbar放置在主窗口上
canvas = tk.Canvas(master=root, height=h, width=w)
scro = tk.Scrollbar(root)
scro.pack(side='right', fill='y')
canvas.pack(side='left', expand=True)


# Frame作为容器放置组件
def refresh_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"), height=frame['height'])


frame = tk.Frame(canvas, height=h)
frame.pack()
frame.bind('<Configure>', refresh_scroll)
# 将Frame添加至Canvas上
canvas.create_window((0, 0), window=frame, anchor="nw")

# 将滚动按钮绑定只Canvas上
canvas.configure(yscrollcommand=scro.set, scrollregion=canvas.bbox("all"))


def Wheel(event):
    canvas.yview_scroll(-1 * (int(event.delta / 120)), "units")


canvas.bind_all('<MouseWheel>', Wheel)
scro.config(command=canvas.yview)
# show_ranks_list()

btn = tk.Button(root, text='刷新', command=main)
btn.place(x=0, y=0)

root.mainloop()