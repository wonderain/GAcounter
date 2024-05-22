import tkinter as tk
from PIL import Image,ImageTk,ImageDraw,ImageFont
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False
from universal import *
from scipy.stats import kstest
from Combobox import *


def get_datetime():
    return datetime.datetime.now().strftime('%Y%m%d')

def json_read(path):
    with open(path,'r',encoding='utf-8')as f:
        text=json.loads(f.read())
    return text
# 列表归一化,输入列表以及一个自定义额外变化项
def list_modify1(unmodi_list:list,append_modi=1):
    modi=sum(unmodi_list)
    return [i*append_modi/modi for i in unmodi_list]
# 给定列数column，返回其归一化权重，权重中间设定为最大，每步之间比值为rate
def set_weights(column,rate):
    weights=[]
    if column%2==0:
        for i in range(int(column/2),0,-1):
            weights.append(1/rate**i)
        for i in range(1,int(column/2)+1):
            weights.append(1/rate**i)
    else :
        for i in range(int(column/2),0,-1):
            weights.append(1/rate**i)
        weights.append(1)
        for i in range(1,int(column/2)+1):
            weights.append(1/rate**i)
    be1=sum(weights)
    return [1/i*be1 for i in weights]


# 计算分差的分布情况，输入：一些分数。每段底分=0.01*段数，则Σ(1/每段低分)=100
# 所以输出100-Σ([1/(i/10+0.01*diff_range_count))能较好表征分布数量和均匀程度(每段10把差不多比较准确了)【现在对上述增加了权重】
def distribution_state(diff_from_max_rank,diff_from_min_rank,score_list,times_list,weights,max_half_diff,partial_list):
    weights_ = [i for i in weights]  # 深拷贝后，处理新的函数
    # 根据和最高最低分的差值重处理权重:如等级分第一，那么weight要从[7.25, 4.8, 3.2, 4.83, 7.25]变成[inf, inf, inf, 4.833333333333334, 7.25]
    #print(diff_from_max_rank,diff_from_min_rank)
    if  diff_from_max_rank<=partial_list[0]:    #从第二个分差段开始
        for index,score_line in enumerate(partial_list):
            if diff_from_max_rank>score_line:       #如果分差>=第几段分数线，那么就将weights_到此为止设置为 float("inf")
                for i in range(index):
                    weights_[i]= float("inf")
                break
    if diff_from_min_rank>=partial_list[-1]:
        for index in range(-1,-len(partial_list)-1,-1): # 从-1到-len(partial_list)
            if diff_from_min_rank<partial_list[index]:       #如果分差>=第几段分数线，那么就将weights_到此为止设置为 float("inf")
                for i in range(-1,index,-1):
                    weights_[i]= float("inf")
                break
    sum_weights_=sum([1/i for i in weights_])
    for index in range(len(weights_)):
        weights_[index]*=sum_weights_
    #print(weights_)
    # 计算在不同分差段的数目
    if not len(score_list):
        return 0
    time_list_=[i for i in times_list]
    for score in score_list:
        if score<-max_half_diff:
            time_list_[-1]+=1
            continue
        for index,score_line in enumerate(partial_list):
            if score>=score_line:
                time_list_[index]+=1
                break
    return 100*(1-sum([1/((times+1)*weights_[index]) for index,times in enumerate(time_list_)]))


# 绘画等级变化
def plot_rank_change(save_path,player_No,players_info,record_info,last_match_date):
    # 比赛序号列表
    match_index=list(players_info[str(player_No)].keys())
    # 最近比赛编号
    player_last_match_index=max([int(i) for i in match_index])
    # 最新比赛日期
    player_last_match_date=record_info[str(player_last_match_index)]['datetime'][:8]
    # 如果该玩家最近一次比赛没有参加，那么就不显示
    if player_last_match_date < last_match_date:
        return


    # 历史等级分列表
    self_history_ranks=list(players_info[str(player_No)].values())
    min_rank=min(self_history_ranks)
    max_rank = max(self_history_ranks)
    plt.cla()
    plt.plot(self_history_ranks)

    # 每日平均值
    means_list=[]
    total=[]
    for index,rank in enumerate(self_history_ranks):
        total.append(rank)
        if len(total)>100:
            del total[0]
        means_list.append(sum(total)/len(total))
    plt.plot(means_list,color='green',linewidth=0.3)
    
    # 获取比赛时间，并提取出时间节点（月+天，如 0425），加入到作图的横轴点上
    x_index_list=[]
    xlabels=[]
    for self_index,match_i in enumerate(match_index):
        if not self_index: continue
        t=record_info[match_i]["datetime"][4:8]
        if t not in xlabels:
            x_index_list.append(self_index)
            xlabels.append(t)
            plt.vlines(self_index,min_rank,max_rank,linestyles='--',colors='grey',linewidth=0.3)
    name=database[str(player_No)]['name']
    if not name:
        name=''
    output='%04d %s'%(int(player_No),name)
    print(player_No,name)
    plt.xticks(x_index_list,xlabels,rotation=-90)
    plt.title(name+' 序号:%s'%player_No,fontsize=20)
    plt.xlim(0,len(match_index))
    # 如果时间节点数量大于一定天数，那么就只提取最近的
    if len(x_index_list) > plot_recent_day:
        start_index = x_index_list[len(x_index_list) - plot_recent_day]
        plt.xlim(xmin=start_index)


    
    plt.savefig(save_path+'/%s.png'%output)
    


# 自身历史数据的KS测试
def self_rank_kstest(player_No,players_info):
    self_history_ranks=list(players_info[str(player_No)].values())
    # 数据中点移动到0
    mid=(max(self_history_ranks)+min(self_history_ranks))/2
    shift=[i-mid for i in self_history_ranks]
    test_result=kstest(shift,'norm')
    return test_result.pvalue


# 1：获取某个玩家所有比赛【当时对手】与【当时他的分差】的平均值（用来描述含金量），注意有两个info，dict都是用str编号的
# 2：获取某个玩家【所有对手】与【他现在的分差】的平均值
# 3：2的分差分布情况
def mean_of_rival_rank_diff(ranks,max_rank,min_rank,player_No,players_info,record_info,times_list,weights,max_half_diff,partial_list):
    recent_diff=0        #最近的对手的分差
    recent_match_index=0    #最近的比赛录入了几场
    now_diff=0              #对手们和自己现在的差
    now_diff_list=[]

    # 自己当前的rank分
    now_self_rank=ranks[int(player_No)]
    #print(player_No,now_self_rank)
    # 和最高/最低分的分差
    diff_from_max_rank=max_rank-now_self_rank
    diff_from_min_rank = min_rank - now_self_rank


    # 取玩家的所有比赛记录,按照降序排放
    player_matchs=sorted(players_info[str(player_No)].items(),key=lambda x:int(x[0]),reverse=True)

    # 百盘平均值
    if player_matchs:
        total=list(players_info[str(player_No)].values())
        if len(total)>100:
            total=total[-100:]
        mean=sum(total)/len(total)
    else:
        mean=0

    # 对每一场比赛的对手进行当时和现在的两种分析
    for match_index,match_rank in player_matchs:
        if match_index=='0':
            continue
        that_match_info=record_info[str(match_index)]
        that_match_now_diff=0           #那场比赛的对手们和自己现在的差

        # 如果该玩家在队伍1，那么对手在队伍2
        for team_index,rival_team_index in [[1,2],[2,1]]:

            if int(player_No) in that_match_info['team%d'%team_index]:
                for rival_player_No in that_match_info['team%d'%rival_team_index]:

                    rival_last_match_index=str(max([int(i) for i in players_info[str(rival_player_No)].keys()]))
                    now_rival_rank=players_info[str(rival_player_No)][rival_last_match_index]                   #对手现在的等级分
                    that_match_now_diff+=(now_rival_rank-now_self_rank)
                    now_diff_list.append((now_rival_rank-now_self_rank))

                that_match_now_diff/=len(that_match_info['team%d'%rival_team_index])

        now_diff+=that_match_now_diff
        if recent_match_index<=10:
            recent_diff+=that_match_now_diff
            recent_match_index+=1
        #print(that_match_diff)
    recent_diff/=recent_match_index
    now_diff/=len(players_info[str(player_No)])-1
    dis=distribution_state(diff_from_max_rank,diff_from_min_rank,now_diff_list,times_list,weights,max_half_diff,partial_list)

    return recent_diff,now_diff,dis,mean


# 显示等级列表
def show_ranks_list():
    match_name=choose_match.getvalue()
    global frame
    players_info={}
    for i in os.listdir('%s/players'%match_name):
        players_info[i[:i.rfind('.')]]=json_read('%s/players/'%match_name+i)
    print('共有%d名玩家在%s的记录中'%(len(players_info),match_name))
    record_info=json_read('%s/record.json'%match_name)

    #最近的一次比赛时间
    last_match_time=record_info[str(len(record_info))]['datetime']
    if last_match_time[8:10] < '12':
        the_day_before_last=datetime.datetime.strptime(last_match_time,'%Y%m%d%H%M%S')+datetime.timedelta(days=1)
        last_match_date=the_day_before_last.strftime('%Y%m%d')
    else:
        last_match_date=last_match_time[:8]


    # 分差可靠性分析，频率段，max_half_diff最大分差(的一半)，step步长
    max_half_diff=120
    step=80
    diff_range_count=int((2*max_half_diff)/step)+2  # 频率段数
    weights=set_weights(diff_range_count,1.5)       # 每个频率段的权重,这里的权重指的是需要跟这个频段玩得更多
    #print(weights)
    partial_list=[i for i in range(max_half_diff,-max_half_diff-1,-step)]   #频率分段点[120,40,-40,-120]
    times_list=[0 for i in range(diff_range_count)] # 频率列表,分成几个分段，如max=120,step=80:[∞,120, 40, -40, -120,-∞]共五段

    # 获取所有玩家当前rank数据
    ranks = {}
    for player_No, rank_info in players_info.items():
        last_match_index = max([int(i) for i in rank_info.keys()])#最后一次参赛的比赛序号
        ranks[int(player_No)]=rank_info[str(last_match_index)]
    max_rank=max(ranks.values())
    min_rank=min(ranks.values())

    # 处理玩家数据
    result=[]
    for player_No,rank_info in players_info.items():
        player_rank=ranks[int(player_No)]
        match_times=len(rank_info)-1
        if match_times>plot_min_count: # 如果满足绘图的参赛数量要求则绘图
            save_path=match_name + '/' + get_datetime()
            makedir(save_path)
            plot_rank_change(save_path,player_No,players_info,record_info,last_match_date)
        diff1,diff2,diff3,mean=mean_of_rival_rank_diff(ranks,max_rank,min_rank,player_No,players_info,record_info,times_list,weights,max_half_diff,partial_list)
        last_match_index = max([int(i) for i in rank_info.keys()]) #最后一次参赛的比赛序号
        last_time=record_info[str(last_match_index)]['datetime'][:8]
        result.append([player_No,round(player_rank),match_times,round(mean),round(diff1),diff3,last_time])
    print('处理后共有%d条玩家数据'%len(result))
    
    # 按顺序打印当前所有玩家rank(比赛少于预定场数不输出)
    img_out_list=[]#放入画布的列表
    for index, info in enumerate(sorted(result, key=lambda x: x[1], reverse=True)):
        img_label = tk.Label(frame, width=130)
        img_label.grid(row=index + 1, column=0)
        img = Image.open('player_database/%s.png' % info[0])
        img = img.resize((130, 30), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(img)
        img_label.config(image=photo)
        img_label.image = photo
        if info[5]>90:
            color='red'
        else:
            color='black'
        tk.Label(frame, text='%s\t%d\t%d\t%d\t%d\t%.1f' % (info[0], info[1], info[2], info[3], info[4], info[5]),fg=color).grid(
            row=index + 1, column=1)
        # 如果少于最低个就不放入画布
        if min_count and info[2]<min_count:
            continue
        img_out_list.append(info)


    # 创建一个画布，图片将输出，每100分分成一列
    max_rank=img_out_list[0][1]
    mar=int(max_rank/100)-1 if max_rank%100==0 else int(max_rank/100)
    min_rank=img_out_list[-1][1]
    mir=int(min_rank/100)-1 if min_rank%100==0 else int(min_rank/100)
    column_num=mar-mir+1    # 按照最高最低分差分成N列
    width_of_column=500 #每列宽度
    new_output_img = Image.new(mode='RGB', size=(width_of_column*column_num, len(img_out_list) * 30 + 125), color='white')
    draw = ImageDraw.Draw(new_output_img)
    font = ImageFont.truetype('YeZiGongChangAoYeHei-2.ttf', 12, encoding='utf-8')

    max_index=0 #所有列最大行数
    match_name = choose_match.getvalue()
    text='等级分表  比赛名:%s  结算日期:%s  制作者:宇宙大王★MAGICA  玩家数据总量:%d  图示玩家数据量(参赛次数>10):%d  总赛次数:%d'%(match_name,get_datetime(),len(result),len(img_out_list),len(record_info))
    print(text)
    draw.text(xy=(0, 5),text=text , fill=(0, 0, 0), font=ImageFont.truetype('YeZiGongChangAoYeHei-2.ttf', 48, encoding='utf-8'))
    for column in range(column_num):
        max_rank_for_column=100*(mar-column+1)  #本列的最大分数限
        min_rank_for_column=100*(mar-column)    #本列的最低分数限
        draw.text(xy=(5 + width_of_column * column, 65), text='%d-%d分段'%(max_rank_for_column,min_rank_for_column), fill=(0, 0, 0), font=ImageFont.truetype('YeZiGongChangAoYeHei-2.ttf', 24, encoding='utf-8'))
        draw.text(xy=(5+ width_of_column*column, 95), text='        ID', fill=(0, 0, 0), font=font)
        draw.text(xy=(150+width_of_column*column, 95), text='数据编号', fill=(255, 0, 0), font=font)
        draw.text(xy=(200+width_of_column*column, 95), text='等级分', fill=(255, 69, 0), font=font)
        draw.text(xy=(250+width_of_column*column, 95), text='比赛次数', fill=(255, 215, 0), font=font)
        draw.text(xy=(300+width_of_column*column, 95), text='平均分', fill=(0, 128, 0), font=font)
        draw.text(xy=(350+width_of_column*column, 95), text='近期对手', fill=(0, 255, 255), font=font)
        draw.text(xy=(400+width_of_column*column, 95), text='可信度1', fill=(0, 139, 139), font=font)
        draw.text(xy=(450 + width_of_column * column, 95), text='最后时间', fill=(138,43,226), font=font)
        column_list=[i for i in img_out_list if max_rank_for_column>=i[1]>min_rank_for_column]
        print('第%d列共%d个数据'%(column+1,len(column_list)))
        for index,info in enumerate(column_list):
            img = Image.open('player_database/%s.png' % info[0])
            img = img.resize((130, 30), Image.ANTIALIAS)
            new_output_img.paste(im=img, box=(0+width_of_column*column, index * 30 + 120))
            draw.text(xy=(150+width_of_column*column, index * 30 + 125), text=str(info[0]), fill=(255, 0, 0), font=font)
            draw.text(xy=(200+width_of_column*column, index * 30 + 125), text=str(info[1]), fill=(255, 69, 0), font=font)
            draw.text(xy=(250+width_of_column*column, index * 30 + 125), text=str(info[2]), fill=(255, 215, 0), font=font)
            draw.text(xy=(300+width_of_column*column, index * 30 + 125), text=str(info[3]), fill=(0, 128, 0), font=font)
            draw.text(xy=(350+width_of_column*column, index * 30 + 125), text=str(info[4]), fill=(0, 255, 255), font=font)
            draw.text(xy=(400+width_of_column*column, index * 30 + 125), text='%.1f' % info[5], fill=(0, 139, 139), font=font)
            draw.text(xy=(440 + width_of_column * column, index * 30 + 125), text=info[6], fill=(138,43,226),font=font)
            if index>max_index:
                max_index=index
    print('最多有%d行'%(max_index+1))

    # 多余的画布裁剪掉
    new_output_img.crop((0,0,width_of_column*column_num,(max_index+1)*30+125)).save('%s/ranks_%s.png'%(match_name,get_datetime()),quality=95)




root = tk.Tk()
w=460
h=400
# 记入统计的最低数量
min_count=10
# 趋势图最低统计数量
plot_min_count=10
# 趋势图统计最近时长
plot_recent_day=5

# 玩家的NO.和数据库数据
database=json_read('player_database/database.json')

root.geometry("%dx%d+100+100"%(w,h))
if not os.path.exists('match_list.json'):
    tk.Label(root,text='\t\t\t未能找到比赛列表').pack()
match_list=json_read('match_list.json')
tk.Label(root,text='\tID\tNo\t等级分\t比赛次数\t平均分\t近期对手\t可信度1').pack()
choose_match=cbbox(root,40,2,8)
choose_match.setvalue(match_list)
# Canvas,Scrollbar放置在主窗口上
canvas = tk.Canvas(master=root,height=h,width=w)
scro = tk.Scrollbar(root)
scro.pack(side='right',fill='y')
canvas.pack(side='left',expand=True)
# Frame作为容器放置组件
def refresh_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"),height=frame['height'])
frame = tk.Frame(canvas,height=h)
frame.pack()
frame.bind('<Configure>',refresh_scroll)
# 将Frame添加至Canvas上
canvas.create_window((0,0),window=frame,anchor="nw")

# 将滚动按钮绑定只Canvas上
canvas.configure(yscrollcommand=scro.set, scrollregion=canvas.bbox("all"))
def Wheel(event):
    canvas.yview_scroll(-1*(int(event.delta/120)), "units")
        
canvas.bind_all('<MouseWheel>',Wheel)
scro.config(command=canvas.yview)
#show_ranks_list()

btn=tk.Button(root,text='刷新',command=show_ranks_list)
btn.place(x=0,y=0)

root.mainloop()
