import os.path
import random
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

# 放空直到出现某个界面（匹配一系列点），注意，这个函数和which_screen的区别在于这个只识别一次，所以不会漏看，而后者主要是判断稳态界面
def till_this_screen(points_name,div,sleep_time,savepath=False,press=False,press_continue=False,ex_function=False,max_wait_time=False):
    """
    放空直到出现某个界面（匹配一系列点）
    :param points_name:界面名字（从setting中读取）
    :param div:色值偏差容许
    :param sleep_time:每次检测间隔时间
    :param savepath:截图保存路径(默认不保存)
    :param press: 按键
    :param press_continue: 是否持续按键，如果True，那每次循环都会按；否则只按一次
    :param max_wait_time:  最大的等待时间，魔人是False
    :return:
    """
    sysexit=get_global('sysexit')
    start_time=time.time()
    while True and not sysexit:
        if max_wait_time:
            if time.time()-start_time > max_wait_time:
                print('长期停留在未知界面')
                return False
        rect,handle=get_window_pos('新热血英豪')
        img=ImageGrab.grab(rect,all_screens=True)
        set_global('window_image', img)
        #   "在房间中": [     20, 800,		1570, 120,		270, 288,   	270, 370,		1100, 114],
        # "在房间中_rgb": [	255, 255, 255,	229, 229, 229,	255, 255, 255,	255, 255, 255,	153, 153, 153],
        pl = color_points_value_list[color_points_name_list.index(points_name)]
        cl = color_points_value_list[color_points_name_list.index(points_name + '_rgb')]
        point_list = [pl[i:i + 2] for i in range(0, len(pl), 2)]
        color_list = [cl[i:i + 3] for i in range(0, len(cl), 3)]
        if press and press_continue:
            Virtual_Keyboard(rect, handle).key_press(press)
            #print('press %s' % press)
        # 如果图片色点满足要求，那么就推出循环
        if pic_match(img, point_list, color_list, div):
            printlog(points_name)
            if savepath:
                img.save(savepath, quality=95)
            if press:
                time.sleep(0.5)
                Virtual_Keyboard(rect, handle).key_press(press)
                # print('press %s' % press)
            return img
        #print('不是'+var_name(point_list))
        # 执行额外函数
        if ex_function:
            threadit(ex_function)
        time.sleep(sleep_time)
        sysexit = get_global('sysexit')
    return False

# 判断是什么界面
def which_screen(max_time=5,delay=0.5,img=False):
    color_points_value_list=get_global('color_points_value_list')
    color_points_name_list=get_global('color_points_name_list')
    sysexit = get_global('sysexit')
    for i in range(max_time):
        if sysexit:
            return False
        if not img:
            img=fetch_image('新热血英豪')
        for points_name in ['在大厅中','在游戏中',"在房间中","回合得分","当前得分","颁奖典礼","最终结果"]:
            pl=color_points_value_list[color_points_name_list.index(points_name)]
            cl = color_points_value_list[color_points_name_list.index(points_name + '_rgb')]
            point_list = [pl[i:i + 2] for i in range(0, len(pl), 2)]
            color_list = [cl[i:i + 3] for i in range(0, len(cl), 3)]
            result=pic_match(img, point_list, color_list, 5)
            if result:
                #print('当前位于'+points_name)
                state_label_text.set(points_name)
                return points_name
        time.sleep(delay)
        sysexit = get_global('sysexit')
    state_label_text.set('未找到界面')
    return False


# 返回变量名
def var_name(var,all_var=globals()):
    return [var_name for var_name in all_var if all_var[var_name] is var][0]


#处理玩家的得分和名字，存入到game_info={'1-1':{1:[score1,team1],2:[score2,team2],...}}中
def del_score(N,n,temp_now_info):
    round_times='%d-%d'%(N,n)
    game_info[round_times]={}
    #print('当回合数据个数:',len(temp_now_info))
    for now_index,info in enumerate(temp_now_info):
        if N+n==2:
            player_index=now_index
        else:
            player_index=which_player(player_name_img,info[0],mode=2,div=400,all_img_crop=(0,3,0,-6))
        printlog('player%d:%s'%(player_index,player_name_img[player_index]['name']),end=' ')
        score=ga_number(info[1])
        printlog('score:%s'%score,end=' ')
        team=info[2]
        printlog('team:%s'%team)
        game_info[round_times][player_index]=[score,team]
    print('当回合录入数据:',game_info[round_times])

# 针对某个房间位置的玩家的发言
def message_for_room_xy(rect, handle,x, y,text):
    VK = Virtual_Keyboard(rect, handle)
    # 中间选择人名
    VK.mouse_middle_press(x, y)
    # 输入
    send_string_to_window(handle, text)
    # 回车
    VK.key_press('ENTER')
    VK.mouse_move_and_back(0,0)

# 获取房间截图，临时保存房间内玩家图片，以便跟下一次对比，并返回所有玩家的编号和信息，若数据库中没有玩家则信息为False
def renew_player_name_in_room(img):
    rect, handle = get_window_pos('新热血英豪')
    settings = get_global('settings')
    nr = settings['img_rect']['房间玩家']
    x_offset, y_offset = settings['img_rect']['房间offset']
    # 先获取房间内所有玩家IDimg，然后和上一刻的img对比，
    temp_room_player_info=[{'img':False,'No_info':False,'skin':False,'ready':0,'weapon_img':False,'weapon_No':False,'toy':True} for i in range(8)]
    # 房间内的改变，用来记录当前的编号跟之前编号的对应，同时也承担着记录当前玩家人数的任务
    room_change=[None,None,None,None,None,None,None,None]
    # 上一刻的img列表
    if len(room_player_info):
        last_img_list=[i['img'] for i in room_player_info]
    for room_index in range(8):
        line=int(room_index/4)
        col=room_index%4
        '''保存当前各位置IDimg'''
        n_r = (nr[0] + col * x_offset, nr[1] + line * y_offset, nr[2] + col * x_offset, nr[3] + line * y_offset)
        if not pic_match(img, [(n_r[0], n_r[1]), (n_r[2], n_r[3])], [(255,255, 255), (255, 255, 255)], 5):
            room_change[room_index] = None
            continue
        name_rect_img=img.crop(n_r).convert('L')
        temp_room_player_info[room_index]['img']=name_rect_img
        '''记录各个位置skin是否加载完毕'''
        skin = [(145 + col * x_offset, 215 + line * y_offset), (145 + col * x_offset, 200 + line * y_offset)]
        skin_rgb = [(192,192,192),(160,160,160)]
        if not pic_match(img,skin,skin_rgb,5):
            temp_room_player_info[room_index]['skin'] = True
        '''记录各个位置玩家的准备状态,未准备=0，绿=1，红=2，蓝=3，个人准备=4'''
        绿准备=[(95,270),(190,260)]
        绿准备_rgb=[(0,80,32),(0,80,32)]
        红准备=[(100,260),(165,260)]
        红准备_rgb=[(112,0,0),(112,0,0)]
        蓝准备=[(90,260),(175,275)]
        蓝准备_rgb=[(0,32,80),(0,32,80)]
        个人准备=[(95,270),(185,275)]
        个人准备_rgb = [(64, 64, 80), (64, 64, 80)]
        ready_state = [[绿准备, 绿准备_rgb], [红准备, 红准备_rgb], [蓝准备, 蓝准备_rgb], [个人准备, 个人准备_rgb]]
        for state in range(4):
            if pic_match(img,ready_state[state][0],ready_state[state][1],5):
                temp_room_player_info[room_index]['ready']=state+1
        # 查看当前玩家IDimg是否在之前的IDimg中,不在则在数据库中检测一下
        if len(room_player_info):
            #print(last_img_list)
            result=min_diff_in_list(last_img_list, name_rect_img, mode=2, div = 500)
            if result is False:
                temp_room_player_info[room_index]['No_info'] = player_database('room').which_player_in_database(
                    name_rect_img)
                printlog('新进入房间：', str(temp_room_player_info[room_index]['No_info']))
                room_change[room_index] = False
            else:
                temp_room_player_info[room_index]['No_info'] = room_player_info[result]['No_info']
                room_change[room_index]=result
        # 如果是第一次的话，那么就直接在数据库检索
        else:
            # 如果有img，那么就检索，没有则不检索
            if  temp_room_player_info[room_index]['img']:
                temp_room_player_info[room_index]['No_info'] = player_database('room').which_player_in_database(name_rect_img)
                printlog('房间内：', str(temp_room_player_info[room_index]['No_info']))
                room_change[room_index] = False
            else:
                room_change[room_index] = None

    '''
    # 遍历房间内的改变，如果是False，那么就是改变了，如果是None，那就是没人，如果是True（即之前的index），则还是老人
    for room_index, rc in enumerate(room_change):
        if rc is False:
            line = int(room_index / 4)
            col = room_index % 4
            print('新进入房间：',temp_room_player_info[room_index]['No_info']['No'])
            #x, y = nr[0] + col * x_offset, nr[1] + line * y_offset
            #message_for_room_xy(rect, handle, x, y, '欢迎')'''

    '''
    # 如果全员准备好了，那就看看装备
    ready_count=0
    number_count=0
    for room_index in range(8):
        if temp_room_player_info[room_index]['ready']:
            ready_count+=1
        if room_change[room_index]!=None:
            number_count+=1
    if ready_count==number_count:
        for room_index in range(8):
            if temp_room_player_info[room_index]['ready']:
                line = int(room_index / 4)
                col = room_index % 4
                x,y=nr[0]+ col * x_offset,nr[1]+ line * y_offset
                # 点击一下已经准备的角色
                Virtual_Keyboard(rect,handle).mouse_press(x,y)
                # 打开装备列表
                Virtual_Keyboard(rect, handle).key_press('F4')
                time.sleep(3)
                # 显示详情装备
                Virtual_Keyboard(rect, handle).mouse_move_and_back(940, 355)
                window_image = ImageGrab.grab(rect, all_screens=True)
                time.sleep(3)
                # 查看装备边框是否正常，否则是带了强化
                if not pic_match(window_image,[(902,408)],[(167,167,167)],5):
                    temp_room_player_info[room_index]['weapon_img']=False
                    temp_room_player_info[room_index]['weapon_No']=False
                    # 关闭装备列表
                    Virtual_Keyboard(rect, handle).key_press('F4')
                    time.sleep(2)
                    message_for_room_xy(rect, handle, x, y, '请不要携带装备强化')
                    continue
                # 是否有小玩意(初始设定为有)
                if pic_match(window_image,[(910,380),(920,380),(930,380),(910,390),(920,390),(930,390),(910,400),(920,400),(930,400)],[(19,41,77) for i in range(9)],5):
                    temp_room_player_info[room_index]['toy'] = False
                else:
                    temp_room_player_info[room_index]['toy'] = True
                    Virtual_Keyboard(rect, handle).key_press('F4')
                    time.sleep(2)
                    message_for_room_xy(rect, handle, x, y, '请不要携带小玩意')
                    continue
                # 获取当前装备的截图，和之前（根据room_change确定之前的）的对比(如果有的话)。如果一致，则直接取用上次的No检索结果，否则检索一下装备No
                now_weapon_img = window_image.crop((865, 372, 905, 412)).convert("L")
                temp_room_player_info[room_index]['weapon_img']=now_weapon_img
                if len(room_player_info) and room_change[room_index] and room_player_info[room_change[room_index]]['weapon_img'] and grey_pixel_diff(now_weapon_img,room_player_info[room_index]['weapon_img'])<100:
                    temp_room_player_info[room_index]['weapon_No']=room_player_info[room_change[room_index]]['weapon_No']
                else:
                    result = min_diff_in_list(
                        [Image.open('weapons/%d.png' % i).convert('L') for i in range(len(os.listdir('weapons')))],
                        now_weapon_img, mode=1, div=100)
                    temp_room_player_info[room_index]['weapon_No']=result
                # 关闭装备列表
                Virtual_Keyboard(rect, handle).key_press('F4')
                time.sleep(2)
    '''


    # 更新确定
    #print('当前房间信息\n',temp_room_player_info)
    room_player_info.clear()
    clear_img_label()
    for index,info in enumerate(temp_room_player_info):
        room_player_info.append(info)
        if info['img']:
            show_img_label(index,False,img=info['img'])


# 对比在结算界面获取到的name_img,从数据库中更新游戏ID和其他信息，如果数据库中有的话，否则返回编号
def upgrade_name_from_database(temp_now_info):
    print('正在从玩家数据库提取/更新数据')
    try:
        for player_index,info in enumerate(temp_now_info):
            #print(info)
            # 对不存在的玩家会自动建立玩家数据库存并返回一个编号No
            database_info=player_database('match').which_player_in_database(info[0])
            if database_info['name']:
                player_name_img[player_index]['name']=database_info['name']
            else:
                player_name_img[player_index]['name'] = '数据库中%d号玩家'%database_info['No']
            player_name_img[player_index]['No']=database_info['No']
    except:
        print(traceback.format_exc())


# 获取当前得分分数
def get_now_team_score(img,N,n):
    global root_dir
    print('正在获取玩家本回合得分')
    settings=get_global('settings')
    round_times='%d-%d'%(N,n)
    nr=settings['img_rect']['团队得分玩家']
    sr=settings['img_rect']['团队得分分数']
    x_offset,y_offset=settings['img_rect']['团队得分offset']
    makedir(root_dir+'/'+round_times)#保存各玩家当前得分截图
    if N+n==2:
        makedir(root_dir+'/name')#保存各玩家当前得分截图
    temp_now_info=[]# 临时记录本回合玩家的名字图片和得分图片[name_im,score_im,team]
    for index in range(8):
        # 用行列表示玩家名字和得分槽位,index同时可以表示截图序号
        line=int(index/2)
        col=index%2
        team=col+1
        n_r=(nr[0]+col*x_offset,nr[1]+line*y_offset,nr[2]+col*x_offset,nr[3]+line*y_offset)
        s_r=(sr[0]+col*x_offset,sr[1]+line*y_offset,sr[2]+col*x_offset,sr[3]+line*y_offset)
        #printlog(line,col,name_rect,s_r)
        if N+n==2 and not pic_match(img,[(n_r[0],n_r[1]),(n_r[2],n_r[3])],[(76,76,76),(76,76,76)],5):
            printlog('player_%d不存在'%index)
            continue
        if N+n>2 and index>len(player_name_img)-1:    #第一回合后就知道有几个玩家，后面跳过
            continue
        score_rect=(s_r[0]+30,s_r[1]+2,s_r[2]-30,s_r[3]-2)
        name_im=img.crop(n_r).convert('L')
        score_im=img.crop(score_rect).convert('L')
        
        if N+n==2:    # 如果是第一回合，则记录玩家的名字截图及其位置，玩家序号从0开始，名字暂时记作序号，后续在线程中更新名字
            name_img_path='%s/name/%d.png'%(root_dir,index)
            player_name_img[len(player_name_img)]={'name':str(len(player_name_img)),'img_path':name_img_path}
            img.crop(n_r).convert('L').save(name_img_path,quality=95)
            total_scores_info.append(0)  # 储存玩家的总得分之和
            each_player_n_win_info.append(0)  # 储存玩家每小局获胜情况
            each_player_N_win_info.append(0)  # 储存玩家每大局获胜情况
            net_scores_info.append(0)
            
        # 保存本回合的玩家名字截图和得分截图
        score_img_path='%s/%s/player%d_score.png'%(root_dir,round_times,index)
        name_im.save('%s/%s/player%d.png'%(root_dir,round_times,index),quality=95)
        score_im.save(score_img_path,quality=95)

        temp_now_info.append([name_im,score_im,team])
    # 处理本回合ID和得分截图对应哪个player_index
    del_score(N,n,temp_now_info)
    # 在线程中访问数据库从而更新名字
    if N+n==2:
        printlog('尝试从数据库获取本局玩家信息')
        threadit(upgrade_name_from_database,temp_now_info)
    return temp_now_info

# 获取奖项信息
def ocr_award_info(img,N,root_dir):
    print('正在获取奖项信息')
    lock.acquire()
    settings = get_global('settings')
    round_times = '%d-%d' % (N, n)
    nr = settings['img_rect']['获奖玩家']
    x_offset, y_offset = settings['img_rect']['获奖offset']
    #各个奖项的背景颜色
    back_color=[(148,219,77),(255,148,77),(219,77,77),(94,148,184),(219,219,219),(168,168,194)]
    award_name=['奋勇杀敌','街头霸王','妙手制胜','铜墙铁壁','太平绅士','红颜薄命']
    temp_info=[]
    for index in range(6):
        line=int(index/2)
        col=index%2
        name_rect=(nr[0]+col*x_offset,nr[1]+line*y_offset,nr[2]+col*x_offset,nr[3]+line*y_offset)
        #print(name_rect)
        award_name_img=img.crop(name_rect)
        award_name_img.save(root_dir+'/%d'%N+award_name[index]+'.png',quality=95)
        if pic_match(img,[(name_rect[0]+1,name_rect[1]),(name_rect[2],name_rect[3])],[back_color[index],back_color[index]],10):
            temp_info.append(False)
            continue
        # 获奖信息使用第一种灰度图匹配方式比较合适（快一丢丢），且需要关闭匹配度限制
        player_index=which_player(player_name_img,award_name_img.convert("L"),mode=1,div=0)
        temp_info.append(player_index)
        printlog(player_index,'是',award_name[index])
    award_info.append(temp_info)
    lock.release()

# 当前回合真实得分
def calculate_real_score(player_index_,N,n):
    round_times='%d-%d'%(N,n)
    print('正在计算%s本回合纯击打分'%player_name_img[player_index_]['name'])
    #name=player_name_img[player_index_]['name']
    #printlog('正在计算%s的本回合真实得分'%name)
    if n==1:
        last_score=0
    else:
        last_score=game_info['%d-%d'%(N,n-1)][player_index_][0]
    try:
        now_score,team=game_info[round_times][player_index_]
    except Exception as e:
        print(traceback.print_exc())
        printlog('###################\n'+round_times,player_index_,'\n',str(game_info))
    win_team=n_win_info[round_times]
    win_or_lose='even' if win_team==0 else 'win' if team==win_team else 'lose'
    win_score=100 if team==win_team else 0
    real_score=now_score-last_score-win_score
    net_scores_info[player_index_]+=real_score
    total_scores_info[player_index_]+=real_score
    return real_score,win_or_lose

#输出玩家所有信息
def print_allinfo(N,n):
    printlog('+++++++++++++++++++++++')
    printlog('【游戏内净得分】')
    for player_index,net_scores in enumerate(net_scores_info):
        name=player_name_img[player_index]['name']
        printlog('%s:%d分'%(name,net_scores))
    printlog('【游戏内总得分】')
    for player_index,total_scores in enumerate(total_scores_info):
        name=player_name_img[player_index]['name']
        printlog('%s:%d分'%(name,total_scores))
    printlog('【赢局数】')
    for player_index, win_times in enumerate(each_player_n_win_info):
        name = player_name_img[player_index]['name']
        printlog('%s:回合%d，大局%d' % (name, win_times,each_player_N_win_info[player_index]))
    printlog('+++++++++++++++++++++++')


# 统计小局
def calculate_n_points(N,n,root_dir,round_end_time):
    round_label_text.set('计分板'+'第%d局-第%d回合'%(N,n))
    round_times='%d-%d'%(N,n)
    lock.acquire()
    win_real_score_dict={}
    lose_real_score_dict={}
    player_count=int(len(player_name_img)/2)
    for player_index in player_name_img:
        real_score,win_or_lose=calculate_real_score(player_index,N,n)
        if win_or_lose=='win':   # 输赢的队伍分别加分
            win_real_score_dict[player_index]=real_score
            each_player_n_win_info[player_index]+=1
        if win_or_lose=='lose':
            lose_real_score_dict[player_index]=real_score
        if real_score<0:# 负分
            c=(8-player_count)/2
            name=player_name_img[player_index]['name']
            printlog('%s负分咯'%name)
    print_allinfo(N,n)
    show_result(N, n)
    lock.release()
    threadit(copy_replay,round_end_time, N, n)

# 没小局分析精彩对局，这里的Nn需要从之前获取，而不能是全局变量（因为会被更改）
# 翻盘：1、失败队伍曾人数领先1个以上，失败队伍总血量曾一度领先一条血
# 搞笑/精彩：在5秒钟内有2个以上玩家突然损失半血以上死去 或者 有玩家10秒内损失了半血以上且没有直接死亡
def analyze_great_time(N, n,replay_path=False):
    if not replay_path or not os.path.exists(replay_path):
        return False

    global root_dir
    round_times = '%d-%d' % (N, n)
    print('正在分析精彩对局',round_times)
    settings = get_global('settings')
    great_time_path=settings["精彩对局存放"]
    if great_time_path=='':
        return False
    if not os.path.exists(great_time_path):
        try:
            os.mkdir(great_time_path)
        except:
            pass
    # 获取胜利队伍
    win_team=n_win_info[round_times]
    if win_team==0:
        return False

    color_points_value_list = get_global('color_points_value_list')
    hp_start_pl = color_points_value_list[color_points_name_list.index("游戏中玩家血1")][:2]
    hp_end_pl = color_points_value_list[color_points_name_list.index("游戏中玩家血1")][2:]
    x_start = hp_start_pl[0]
    x_end = hp_end_pl[0]
    x_width=x_end-x_start+1

    dealed_tp_hps=[]  # 处理过的hp信息，删除了跟玩家数量不相等的部分
    player_count=len(player_name_img)
    for i in hp_info[round_times]:
        tp,hps=i
        member_count=0
        for index,hp in hps.items():    # 如果HP值不为False，那么就是一个人头
            if not hp is False:
                member_count+=1
        if member_count == player_count:    #如果人头数等于玩家数(结算界面的)就被收录
            dealed_tp_hps.append(i)

    tps=len(dealed_tp_hps) # 时间点个数
    #print(hp_info[round_times])
    start_time=hp_info[round_times][0][0]
    end_time=hp_info[round_times][-1][0]

    revers_tp=[]   # 大优势的时间点
    for tp,tp_info in dealed_tp_hps:
        team1_alive = 0
        team2_alive = 0
        team1_total_hp = 0
        team2_total_hp = 0
        for player_ingame_index,hp in tp_info.items():
            if hp is False:
                continue
            if player_ingame_index<=4 and hp>0:
                team1_alive+=1
                team1_total_hp+=hp
            if player_ingame_index>4 and hp>0:
                team2_alive+=1
                team2_total_hp+=hp
            if team1_alive and team2_alive:
                if win_team==2 and team1_alive>team2_alive and team1_total_hp>team2_total_hp+x_width:
                    revers_tp.append([tp,team1_alive,team1_total_hp,team2_alive,team2_total_hp])
                elif win_team==1 and team1_alive<team2_alive and team1_total_hp<team2_total_hp-x_width:
                    revers_tp.append([tp,team1_alive,team1_total_hp,team2_alive,team2_total_hp])
    if len(revers_tp):
        name_type=os.path.basename(replay_path)
        name=name_type.replace('repkar','')
        with open('%s/%s.txt'%(great_time_path,name),'w' ,encoding='utf-8') as f:
            f.write('获胜队伍： %d\n'%win_team)
            for tp,team1_alive,team1_total_hp,team2_alive,team2_total_hp in revers_tp:
                f.write('%s秒时，对手处在大优势阶段\n'%(tp-start_time))
                f.write('\t双方比较：%s %s %s %s'%(team1_alive,team1_total_hp,team2_alive,team2_total_hp))
            f.write('历时共%s秒\n'%(end_time-start_time))
            f.write('\n====================\n')
            for tp, tp_info in hp_info[round_times]:
                f.write('时间点：%s秒\n'%(tp-start_time))
                for player_ingame_index,hp in tp_info.items():
                    f.write('\t\t'+str(hp))
                f.write('\n')
        shutil.copy(replay_path,'%s/%s'%(great_time_path,name_type))
    else:
        print('本场对局没有精彩点')



# 输出为elo准备的数据，即仅计算大局输赢，输出为{'match_name':比赛名,'datetime':datetime,'team1':[p1,p2],'team2':[p3,p4],'win':0,'detail':}，win是赢的队伍编号,0标识平局
def output_elo_data(N,n,root_dir,ifsave=False):
    lock.acquire()
    makedir('elo_uninput_data')
    round_times = '%d-%d' % (N, n)
    #print(N_win_info,N)
    win = N_win_info[N-1]
    settings = get_global('settings')

    round_info=game_info[round_times]
    team1=[]
    team2=[]
    for player_index,info in round_info.items():
        if info[1]==1:
            team1.append(player_name_img[player_index]['No'])
        else:
            team2.append(player_name_img[player_index]['No'])
    dt=get_datetime()
    record={"host_name":settings["host_name"],'match_name':show_match_cbbox.getvalue(),'datetime':dt,'team1':team1,'team2':team2,'win':win}
    lock.release()
    if ifsave:
        json_write('elo_uninput_data/%s.json'%dt,record)
    else:
        elo_open(show_match_cbbox.getvalue()).input_new_record(record)
    json_write('%s/%s/%s.json' %(root_dir,round_times,dt) , record)


# 显示比赛进程和结果
def show_result(N,n):
    mode = mode_list.index(show_mode_cbbox.getvalue())
    if mode == 1:
        show_score(N, n)
    else:
        show_win(N, n)
# 清空IDimg显示
def clear_img_label():
    for i in player_name_img_label_list:
        i.configure(image=None)
        i.image = None
    for i in points_text_list:
        i.set('')
    show_window.update()
# 在显示面板显示ID img
def show_img_label(index,img_path,img=False):
    if not img:
        img = Image.open(img_path)
        img=img.resize((130,30), Image.ANTIALIAS)
    photo=ImageTk.PhotoImage(img)
    player_name_img_label_list[index].config(image=photo)
    player_name_img_label_list[index].image = photo
    show_window.update()

#把剪切板内容粘贴到qq窗口
def send_result_img_to_window(round_times):
    time.sleep(0.2)
    img = fetch_image('tk')
    settings=get_global('settings')
    if settings["显示窗口每回合截图"]:
        img.save(root_dir + '/' + round_times + '结果.png', quality=95)
    try:
        if hwndcbbox.send_result_handle:
            output = BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            setImage(data)
            pos,handle=get_window_pos(hwndcbbox.send_result_handle)
            #ShowWindow(handle, win32con.SW_SHOW)    #显示窗口
            time.sleep(0.1)  # 等待剪切板空闲
            win32gui.SendMessage(handle, win32con.WM_PASTE, 0, 0)
            time.sleep(0.1)  # 等待剪切板空闲
            win32gui.SendMessage(handle, win32con.WM_KEYDOWN, 13, 0)
            time.sleep(0.1)
            win32gui.SendMessage(handle, win32con.WM_KEYUP, 13, 0)
    except:
        printlog(traceback.print_exc())


# 展现赢数
def show_win(N,n):
    global root_dir
    round_times = '%d-%d' % (N, n)
    clear_img_label()
    for player_index, win_times in enumerate(each_player_n_win_info):
        show_img_label(player_index, '%s/name/%d.png' % (root_dir, player_index))  # 展现名字
        text='小%d大%d'%(win_times,each_player_N_win_info[player_index])
        points_text_list[player_index].set(text)
    send_result_img_to_window(round_times)

# 展现游戏得分
def show_score(N,n):
    global root_dir
    round_times = '%d-%d' % (N, n)
    clear_img_label()
    for player_index, net_scores in enumerate(net_scores_info):
        show_img_label(player_index, '%s/name/%d.png' % (root_dir, player_index))  # 展现名字
        text = '%d | %d' % (net_scores, total_scores_info[player_index])
        points_text_list[player_index].set(text)
    send_result_img_to_window(round_times)

# 统计大局
def calculate_N_points(N,n,root_dir):
    lock.acquire()
    round_label_text.set('计分板'+'第%d局-第%d回合'%(N,n))
    printlog('================\n统计第%d大局积分中'%N)
    round_times='%d-%d'%(N,n)
    player_count=int(len(player_name_img)/2)
    # 计算双方对局分（即第三小局不计算奖项的分数和）
    team1_score=0
    team2_score=0
    for player_index,info in game_info[round_times].items():
        if info[1]==1:
            team1_score+=info[0]
        else:
            team2_score+=info[0]
    # 失败队伍判定(根据双方最终分),同时计算奖项积分
    team1_final_score=team1_score
    team2_final_score=team2_score
    award_score=[200,150,150,100,-50,-50]
    for i,player_index in enumerate(award_info[N-1]):
        if player_index is False:   # 否则False和0区分不开
            continue
        total_scores_info[player_index]+=award_score[i]
        team=game_info[round_times][player_index][1]
        if team==1:
            team1_final_score+=award_score[i]
        else:
            team2_final_score+=award_score[i]
    win_team=1 if team1_final_score>team2_final_score else 0 if team1_final_score==team2_final_score else 2
    # 总东西里面加
    N_win_info.append(win_team)
    printlog('当前玩家胜局统计：',N_win_info)
    show_result(N,n+1)
    print_allinfo(N,n+1)
    lock.release()
    printlog('========================\n')

#复制replay文件（先停10秒，然后寻找在这期间的replay文件）
def copy_replay(round_end_time,N, n):
    global root_dir
    time.sleep(10)
    try:
        replay_path = get_global('settings')['replay_path']
    except:
        replay_path = False
    if replay_path and os.path.exists(replay_path):
        now_time=time.localtime()
        # 尝试五次，寻找repaly文件，遍历文件名最大的5个
        for times in range(5):
            l=[i for i in os.listdir(replay_path) if '.repkar' in i]
            l.sort(reverse = True)
            replay_list=l[:5]
            for i in replay_list:
                if round_end_time<=time.strptime(i,"amped_replay_%Y%m%d_%H%M_%S.repkar")<=now_time:
                    replay_exists=i
                    shutil.copy(replay_path + '/' + replay_exists, root_dir + '/' + replay_exists)
                    printlog('replay文件已转存:%s' % replay_exists)
                    analyze_great_time(N, n, replay_path=replay_path + '/' + replay_exists)
                    return False



# 房间里的人是否换了新的一波？
def whether_new_round():
    now_round_room_player_img=[i['img'] for i in room_player_info if i['img']]
    if len(last_round_room_player_img)==len(now_round_room_player_img):
        if whether_all_same_img(last_round_room_player_img, now_round_room_player_img, mode=2, div=500):
            #print('本局游戏相比上一局人员无变动')
            return False
    last_round_room_player_img.clear()
    for img in now_round_room_player_img:
        last_round_room_player_img.append(img)
    printlog('本局游戏相比上一局人员有变动')
    return True

# 界面变换，从游戏中到房间内的操作
def from_ingame2room(handle):
    screen_state = which_screen()
    while screen_state != "最终结果2" and  screen_state != "在房间中":
        screen_state = which_screen()
        if screen_state =='在游戏中':
            auto_change_view_in_game()
        if screen_state in ["回合得分", "当前得分", "颁奖典礼","最终结果","最终结果2"]:
            Virtual_Keyboard(0, handle).key_press('F5')
        time.sleep(1)
    if screen_state == "最终结果2":
        time.sleep(3)
        Virtual_Keyboard(0, handle).key_press('F5')
        print('未记录的一局结束')

# 从截图获取第几号(但是这个序号跟别的数据不一样)玩家的HP值
def get_player_hp(img,index):
    color_points_value_list = get_global('color_points_value_list')
    frame=color_points_value_list[color_points_name_list.index("游戏中玩家框%d" % index)]
    frame_rgb=color_points_value_list[color_points_name_list.index("游戏中玩家框_rgb")]
    hp_start_pl = color_points_value_list[color_points_name_list.index("游戏中玩家血%d" % index)][:2]
    hp_end_pl = color_points_value_list[color_points_name_list.index("游戏中玩家血%d" % index)][2:]
    # 如果玩家的血条点不在这几个颜色之间，且没检测到框 那么就是有问题
    if img.getpixel(tuple(hp_end_pl)) not in [(0,0,0),(0,167,0),(255,167,0),(255,0,0),(153, 220, 153),(255, 220, 153),(112, 112, 112)] or not pic_match(img,[frame],[frame_rgb],div=8):
        return False
    x_start=hp_start_pl[0]
    x_end=hp_end_pl[0]
    y=hp_start_pl[1]
    black=(0,0,0)
    red=(255,0,0)
    green=(0,167,0)
    yellow=(255,167,0)
    shining_green=(153, 220, 153)
    shining_yellow=(255, 220, 153)
    greens=[green,shining_green]
    yellows=[yellow,shining_yellow]
    x_middle=int((x_end+x_start)/2) # 中点
    x_width=x_end-x_start+1
    # 先看一下最右侧是否绿色
    if img.getpixel(tuple(hp_end_pl))==green:
        return 2*x_width
    # 如果第一个点是黑色，那么就是死了
    elif img.getpixel((x_start, y))==(0,0,0):
        return 0
        # 如果第2个点是黑色，那么就是意志力
    elif img.getpixel((x_start+1, y)) == (0, 0, 0):
        return 1
    # 如果第一个点是红色且最后一个点是红色，那么返回字符串(此时应该不会是还没建立info的时候)，沿用上一次的颜色
    elif img.getpixel((x_start, y)) == (255, 0, 0) and img.getpixel((x_end, y)) == (255, 0, 0):
        return '红色'
    # 如果第一个点是红色且最后一个点是黑色，那么就是空血
    elif img.getpixel((x_start, y)) == (255, 0, 0) and img.getpixel((x_end, y)) == (0, 0, 0):
        return 0
    # 如果有一些银色点，是密探zc后的特效
    elif img.getpixel((x_start, y)) == (112, 112, 112) and img.getpixel((x_end,y)) ==(16, 16, 16):
        return '密探特效'
    # 如果中间点是绿色，那么往右半边看，看到绿色之外的颜色停止
    elif img.getpixel((x_middle,y))in greens:
        for x in range(x_middle,x_end+1):
            if img.getpixel((x,y)) not in greens:
                return x+x_width-x_start
    elif img.getpixel((x_middle,y)) in yellows:
        # 如果中间点是黄色,且最右也是黄色，那么往左半边看，看到绿色停止;如果都没找到，那么返回半血
        if img.getpixel((x_end,y)) in yellows:
            for x in range(x_middle,x_start-1,-1):
                if img.getpixel((x,y))in greens:
                    return x+x_width-x_start+1
            return x_width
        # 如果中间点是黄色，但是最右不是黄色，那么往右边看，不是黄色的点为止
        else:
            for x in range(x_middle, x_end+1):
                if img.getpixel((x,y))not in yellows:
                    return x-x_start
    # 否则就是四分之一血以下，直接向左看
    else :
        for x in range(x_middle, x_start - 1, -1):
            if img.getpixel((x, y)) in yellows:
                return x- x_start+1
    printlog('%s号位血量检测存在遗漏情况，请确认是否代码问题'%index)
    return False

# 记录血量变化
def record_hp():
    global root_dir, N, n
    round_times = '%d-%d' % (N, n)
    img = get_global('window_image')
    if round_times  not in hp_info:
        hp_info[round_times]=[]
    t=time.time()
    # 玩家1-8号血量计数
    temp= {}
    member_count=0  # 不是FALSE的人数计数，如果人数不等于游戏人数，那么这个时间点不会被录用
    for index in range(1, 9):
        result = get_player_hp(img, index)
        if type(result)==type(""):
            try:
                temp[index]=hp_info[round_times][-1][1][index]
                member_count+=1
            except:
                print('%s血量情况出现错误'%result,traceback.format_exc())
                temp[index] = False
        elif result is False:
            temp[index] = False
        else:
            temp[index] = result
            member_count += 1
    #如果人数不等于游戏人数，那么这个时间点不会被录用,但是这里第一局没法使用，所以就不加这个判断，但是相应的在分析精彩对局的时候要处理这个问题(那时候已经读取了玩家的数量)
    #if member_count==len(player_name_img):
    hp_info[round_times].append([t,temp])
    #print(len(hp_info[round_times]),hp_info[round_times][-1])



# 这个函数仅在游戏中检测循环里使用，在游戏中的时候自动改变视野(记录一次某个点位，超过一定次数就会按V,或者当前监控的角色位)，在主程序刚开始时设定全局变量
def auto_change_view_in_game():
    # 在有血的玩家中随机选一个作为视角
    def random_choose_view_index(hps):
        # 存在血量的玩家序号，从中随机取一个
        try:
            exist_player_index_list=[index for index in range(1,9) if hps[index]]
            index=random.sample(exist_player_index_list,1)[0]
            Virtual_Keyboard(0, handle).key_press(str(index))
            set_global('last_sight', index)
        except:
            print(hps,traceback.format_exc())

    global root_dir, N, n
    round_times = '%d-%d' % (N, n)
    sight_set=get_global('sight_set')
    img=get_global('window_image')
    if not which_screen(img=img) =='在游戏中':
        return False

    # 上一个视角，如果是False，那么就是第一次，随机调换一个视角(这个只在正式记录开始后使用n>0)
    last_sight = get_global('last_sight')
    if n and last_sight is False:
        if round_times in hp_info and len(hp_info[round_times]):
            hps = hp_info[round_times][0][1]
            random_choose_view_index(hps)

    # 记录血量变化
    record_hp()
    sight_point_color=[img.getpixel((50,80)),img.getpixel((50,850)),img.getpixel((800,450))]
    sight_set.append(sight_point_color)

    # 当前视角下的玩家血量，如果为零，那么换一个有血的
    if round_times in hp_info and len(hp_info[round_times]):
        hps = hp_info[round_times][-1][1]
        if last_sight:
            #print('检测当前视角玩家血量为:',hps[last_sight],hp_info[round_times][-1][0])
            if not hps[last_sight]:
                print('因视角玩家死亡或不存在而切换视角')
                random_choose_view_index(hps)
                return True

    # 当视野点超过5个开始，准备切换视野。如果很久没有变换视野或者当前视角下的玩家血量是0，那么就搜索一下有血的玩家，然后按对应的小数字键
    if len(sight_set)>=6:
        del sight_set[0]
        count=0
        # 对之前的点集，如果其中某个点和中心点一直保持一直，那就+1
        for i in sight_set:
            if  pic_match(img,[[800,450]],[i[2]],10):
                #print('中心点未动')
                for j in range(2):
                    if pic_match(img,[[[50,80],[50,850]][j]],[i[j]],10):
                        #print('上下点未动',count+1)
                        count+=1
                        break
        if count==len(sight_set):
            if round_times in hp_info and len(hp_info[round_times]):
                # 最近的上一次hp记录
                hps =hp_info[round_times][-1][1]
                print('因画面停顿切换视角')
                random_choose_view_index(hps)
                return True

def main():
    global root_dir,N,n
    set_global('sight_set',[]) #视野调整用,储存点的合集
    set_global('last_sight',False) #储存上一个视野的编号
    rect, handle = get_window_pos('新热血英豪')
    sysexit=get_global('sysexit')
    N = 1
    n=0
    max_game_run_times=get_global('settings')["最大循环次数"]
    # 判断在什么界面
    screen_state = which_screen(max_time=20)
    # 如果在游戏中，那么需要经常按F5，直到回到房间里
    while screen_state not in ['在游戏中','在房间中']:
        if screen_state == '在大厅中':
            print('当前在大厅中')
            return False
        screen_state = which_screen(max_time=20)
        if screen_state in ["回合得分","当前得分","颁奖典礼","最终结果"]:
            Virtual_Keyboard(0, handle).key_press('F5')
        time.sleep(2)
    if screen_state == '在游戏中':
        from_ingame2room(handle)
    for game_run_times in range(1,max_game_run_times+1):#最大记录局(我都不信有人能开15大局以上不掉)
        room_img = till_this_screen('在房间中', 5, 1)
        renew_player_name_in_room(room_img)
        temp_img = fetch_image('新热血英豪')
        while img_match(temp_img, '在房间中', 5):
            renew_player_name_in_room(temp_img)
            time.sleep(0.2)
            temp_img = fetch_image('新热血英豪')
        for n_ in range(1,4):#3小局
            n=n_
            reset_round()
            if N+n==2:
                hp_info.clear()
            # 当新一批人开始游戏的时候，记录一下大家的IDimg，和之前对比，并重新放一个文件夹
            if n==1 and whether_new_round():
                N=1
                # 如果不是刚开游戏第一局，那就需要更新文件夹了
                if game_run_times!=1:
                    root_dir = 'general_record/%s' % get_datetime()
                    #print(root_dir)
                    makedir(root_dir)
                    makedir('%s/room_name' % root_dir)
                    makedir('%s/name' % root_dir)
                for index, img in enumerate([i['img'] for i in room_player_info]):
                    if img:
                        img.save('%s/room_name/%d.png' % (root_dir, index))
            round_times='%d-%d'%(N,n)
            printlog('正在记录:'+round_times)
            # 重置所有信息
            if N + n == 2:
                reset_match_info_record()
            # 等待游戏结束
            till_this_screen('游戏结束',5,1,ex_function=auto_change_view_in_game)
            round_end_time=time.localtime()  #每个回合结束时间
            if sysexit:
                return False

            # 记录每小局胜利队伍
            win_info_img=till_this_screen('回合得分',5,0.2,savepath='%s/%s-回合得分.png'%(root_dir,round_times),press='F5')
            if sysexit:
                return False
            if img_match(win_info_img,"红方胜利",5):
                n_win_info[round_times]=1
            elif img_match(win_info_img,'蓝方胜利',5):
                n_win_info[round_times]=2
            else:
                n_win_info[round_times]=0
            printlog('%s胜利者：%d'%(round_times,n_win_info[round_times]))

            #记录每小局每个玩家的得分和队伍
            now_score_img=till_this_screen('当前得分',5,0.3,savepath='%s/%s-当前得分.png'%(root_dir,round_times),press='F5')
            if sysexit:
                return False
            get_now_team_score(now_score_img,N,n)
            if n==3 and len(player_name_img)>2: #如果是最后一小局，且游戏人数>2，要记录获奖信息
                award_img=till_this_screen('颁奖典礼',5,0.3)
                Virtual_Keyboard(0,handle).key_press('F5')
                if sysexit:
                    return False
                #award_img.save('%s/%d-获奖信息.png'%(root_dir,N),quality=95)

            calculate_n_points(N,n,root_dir,round_end_time)
        # 虽然不记录截图识别，但是需要记录一堆空的获奖记录防止后续计算出错
        if len(player_name_img) > 2:
            ocr_award_info(award_img, N, root_dir)
        else:
            award_info.append([False, False, False, False, False, False])
        def N_deal():
            printlog('获奖信息:',award_info[-1])
            calculate_N_points(N,n,root_dir)
            output_elo_data(N, n,root_dir,ifsave=True)
            save_all_game_info()
        threadit(N_deal)
        if sysexit:
            return False
        from_ingame2room(handle)
        N += 1

sysexit=get_global('sysexit')
sysexit=False


def atexitf():
    log=get_global('log')
    set_global('sysexit', True)
    global root_dir
    makedir(root_dir)
    with open('%s/log.txt'%root_dir,'w',encoding='utf-8')as f:
        f.write(log)
    save_all_game_info()
atexit.register(atexitf)


# 房间中第几个位置的玩家信息，包含玩家No_info、玩家造型加载状态、玩家准备状态、玩家装备、玩家是否小玩意,=[{...},{...},{...}]
room_player_info=[]
# 上一轮玩家的roomIDimg
last_round_room_player_img=[]
net_scores_info = []  # 储存玩家的净得分(每回合真实得分)总和
total_scores_info = []  # 储存玩家的总得分之和
each_player_n_win_info = []  # 储存玩家每小局获胜情况
each_player_N_win_info = []  # 储存玩家每大局获胜情况
hp_info={}  # 储存每小局的血量变化,hp_info={'1-1':[[t1,{1:252,2:123,3:False...}],[t2,{1:252,2:123,3:False...}]]}  }
game_info = {}  # 储存每小局游戏信息，game_info={'1-1':{1:[score1,team1],2:[score2,team2],...}}
n_win_info = {}  # 储存每小局胜利队伍,game_info={'1-1':1,'1-2':0} 平局为0
N_win_info=[]   # 储存每大局胜利队伍
award_info = []  # 储存每大局的获奖信息,award_info=[[p1,False,p1,False,p3,p4,p5],...]
player_name_img = {}  # 储存玩家的图片位置，={1:[name,img_path],2:[name,img_path]...}

# 保存所有游戏信息
def save_all_game_info():
    global root_dir
    json_write(root_dir+'/all_game_info.json',{'小局获胜信息':n_win_info,'大局获胜信息':N_win_info,'得分信息':game_info,'获奖信息':award_info})

#每一波新人都需要重置一下记录（延迟）
def reset_match_info_record():
    net_scores_info.clear()
    total_scores_info.clear()
    each_player_n_win_info.clear()
    each_player_N_win_info.clear()
    game_info.clear()
    n_win_info.clear()
    N_win_info.clear()
    award_info.clear()
    player_name_img.clear()

# 每一轮都需要重置的内容(提前)
def reset_round():
    set_global('sight_set', [])  # 视野调整用,储存点的合集
    set_global('last_sight', False)  # 储存上一个视野的编号

if __name__ =='__main__':
    #settings=get_settings()
    # 窗口置顶
    rect,handle=get_window_pos('新热血英豪')
    win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE | win32con.SWP_NOOWNERZORDER | win32con.SWP_SHOWWINDOW | win32con.SWP_NOSIZE)
    show_window=tk.Tk('GA计分板')
    show_window.geometry('200x420')
    tk.Label(show_window,text='玩家昵称',font=('微软雅黑',9,'bold')).place(x=15,y=35)
    #tk.Label(show_window,text='排名',font=('微软雅黑',9,'bold')).place(x=95,y=35)
    tk.Label(show_window,text='信息',font=('微软雅黑',9,'bold')).place(x=155,y=35)
    round_label_text=tk.StringVar()
    round_label_text.set('计分板')
    round_label=tk.Label(show_window,textvariable=round_label_text,fg='red',font=('微软雅黑',15,'bold'),height=1)
    round_label.pack()
    left_frame=tk.Frame(show_window,height=30*8,width=130)
    left_frame.place(x=5,y=65)
    right_frame=tk.Frame(show_window,height=30*8,width=70)
    right_frame.place(x=130,y=70)
    player_name_img_label_list=[]   #用于显示玩家名的图片的label
    points_text_list=[]             #用于显示玩家分数的label对应的StringVar()
    for index in range(8):
        label=tk.Label(left_frame,width=130)
        label.place(x=0,y=index*30)
        points_text=tk.StringVar()
        points_label=tk.Label(right_frame,textvariable=points_text,font=('微软雅黑',9,'bold'))
        points_label.place(x=0,y=index*30)
        player_name_img_label_list.append(label)
        points_text_list.append(points_text)

    '''选择模式'''
    mode_list=['赢局数模式','游戏得分模式']
    show_mode_cbbox = cbbox(show_window, x=5, y=310, width=12)
    show_mode_cbbox.setvalue(mode_list)
    def show_result_(*event):
        global N,n
        show_result(N,n)
    show_mode_cbbox.bindselect(show_result_)
    '''选择ELO比赛'''
    match_list = json_read('match_list.json')
    show_match_cbbox = cbbox(show_window, x=5, y=370, width=12)
    show_match_cbbox.setvalue(match_list)
    '''选择句柄按钮'''
    hwndcbbox=handle_cbbox(show_window,x=5,y=340,width=12)
    tk.Button(show_window,text='刷新窗口句柄',command=hwndcbbox.get_all_handel_name).place(x=115,y=335)
    lock=threading.Lock()
    '''显示当前状态'''
    state_label_text = tk.StringVar()
    state_label_text.set('当前状态')
    state_label=tk.Label(show_window,textvariable=state_label_text)
    state_label.place(x=75,y=395)


    makedir('general_record')
    global root_dir
    root_dir = 'general_record/%s' % get_datetime()
    makedir(root_dir)
    makedir('%s/room_name' % root_dir)
    makedir('%s/name' % root_dir)
    threadit(main)


    show_window.mainloop()
    set_global('sysexit', True)
    atexitf()

    

