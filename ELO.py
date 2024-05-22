from universal import *
from Player_Database import *

# 由于建立了玩家数据库，所以ELO中不记录名字而是记录玩家的No
class elo_open():
    def __init__(self,match_name,rootpath='./'):
        self.rootpath=rootpath
        self.match_name=match_name
        self.match_path=self.rootpath+self.match_name
        self.Ks_list=False
        if not os.path.exists(rootpath+match_name):
            makedir(self.match_path)
            makedir(self.match_path+'/players')
            json_write(self.match_path+'/record.json',{})
            self.new_match = ['settings','Ks']
        else:
            if not os.path.exists(self.match_path+'/record.json'):
                printlog('比赛类型【%s】的过往记录缺失'%match_name)
                return False
            self.Ks_list=self.read_Ks()
            self.settings=json_read(self.match_path+'/settings.json')
            self.new_match =[]
            match_list=json_read('match_list.json')
            if self.match_name not in match_list:
                match_list.append(self.match_name)
            json_write('match_list.json',match_list)

    # 设置初始信息，包含：{'default_init_rank':默认初始等级分,'init_round':定位赛局数,'init_round_K':定位赛K值,'init_round_max_D':定位赛最大分差}
    def set_init(self,settings):
        """
        设置初始信息
        :param settings:{'default_init_rank':默认初始等级分,'init_round':定位赛局数,'init_round_K':定位赛K值,'init_round_max_D':定位赛最大分差}
        """
        for i in ['default_init_rank','init_round','init_round_K','init_round_max_D',"whether_int_rank"]:
            if i not in settings:
                printlog('初始信息缺少%s信息'%i)
                return False
        json_write(self.match_path+'/settings.json',settings)
        self.settings=settings
        if 'settings' in self.new_match:
            self.new_match.remove('settings')

    # 读K值列表
    def read_Ks(self):
        Ks_list=json_read(self.match_path+'/Ks.json')
        if len(Ks_list):
            return Ks_list
        else:
            return False

    # 设置一系列K值，[最小值,K]，如单挑[[900,5],[800,10],[700,15],[600,20],[400,30],[200,20],[0,10]]
    def set_Ks(self,Ks_list:list):
        if not len(Ks_list):
            return '预设定的K值系列空'
        for index in range(len(Ks_list)-1):
            K=Ks_list[index]
            if len(K) !=2:
                return '预设定的K值系列中，第%d个不符合[最小值，k]的规范'%index
            if  K[0]<=Ks_list[index+1][0] or K[1]<=0:
                return '预设定的K值系列中，第%d个或第%d个不符合'%(index,index+1)
        if Ks_list[-1][0]!=0:
            return '预设定的K值系列中，最后一个分段需要为0起步'
        json_write(self.match_path+'/Ks.json',Ks_list)
        self.Ks_list=Ks_list
        if 'Ks' in self.new_match:
            self.new_match.remove('Ks')
        return False

    # 设定一个新玩家。基本json数据格式为{比赛编号(新玩家未参与比赛，所以使用比赛编号0):等级分},如{0:1200,15:1234}
    def set_new_player(self,No,init_rank=False):
        """
        设定一个新玩家，需要先判定比赛是否初始化
        储存数据格式为
        {比赛编号(新玩家未参与比赛，所以使用比赛编号0):等级分},如{0:1200,15:1234}
        :param No:数据库中玩家序号
        :param init_rank:自定义初始等级分
        :return:
        """
        if len(self.new_match):
            printlog('比赛信息未初始化')
            return False
        try:
            os.mkdir(self.match_path+'/players')
        except:
            pass
        if '%d.json'%(No) in os.listdir(self.match_path+'/players'):
            printlog('已存在第%d号玩家-%s的信息'%(No,player_database().get_No_name(No)))
            return False
        if init_rank:
            set_init_rank=init_rank
        else:
            set_init_rank=self.settings['default_init_rank']
        json_write('%s/players/%d.json'%(self.match_path,No),{0:set_init_rank})
        return {0:set_init_rank}


    # 输入一条新比赛记录{'datetime':datetime,'team1':[p1,p2],'team2':[p3,p4],'win':0,'during':50},during是比赛持续时间，win是赢的队伍编号,0标识平局
    # default_init_new_player是默认初始化玩家
    def input_new_record(self,match_data:dict,calculate_new=True,default_init_new_player=True):
        if len(self.new_match):
            printlog('比赛信息未初始化')
            return False
        if not len(match_data):
            return False
        if 'datetime' not in match_data or 'team1' not in match_data or 'team2' not in match_data:
            return False
        if type(match_data['team1'])!=type([]) or not len(match_data['team1']):
            return False
        if type(match_data['team2'])!=type([]) or not len(match_data['team2']):
            return False

        '''判断是否有玩家未初始化'''
        no_player_list=[]
        for player_No in match_data['team1']+match_data['team2']:
            if not self.read_player(player_No):
                no_player_list.append(player_No)
        if len(no_player_list):
            for player_No in no_player_list:
                #print(player_No)
                printlog('%d-%s'%(player_No,player_database().get_No_name(player_No)),end=',')
            printlog('以上玩家在本项赛事中没有档案')
            if default_init_new_player:
                printlog('将自动按照默认设定建立档案')
                for player_No in no_player_list:
                    self.set_new_player(player_No)
            else:
                printlog('请建立档案后再输入相关对局记录')
                return False

        match_record=json_read(self.match_path+'/record.json')
        match_data['match_index']=len(match_record)+1
        match_record[len(match_record)+1]=match_data
        json_write(self.match_path+'/record.json',match_record)
        if calculate_new:
            self.calculate_new_record(match_info=match_data)

    # 计算最新的一场比赛，更新数据
    def calculate_new_record(self,match_info=False,default_init_new_player=True):
        # 如果不输入比赛信息，则自动提取最近的比赛
        if not match_info:
            match_record=json_read(self.match_path+'/record.json')
            match_info=match_record[len(match_record)]
        match_index=match_info['match_index']
        team_rank=[0,0]
        player_ranks_dict={}
        for i in range(2):
            for player_No in match_info['team%d'%(i+1)]:
                player_record=self.read_player(player_No)
                player_last_rank=player_record[max(player_record.keys())]
                #printlog('%s : %d'%(player_No,player_last_rank))
                team_rank[i]+=player_last_rank
                player_ranks_dict[player_No]=player_last_rank
        printlog('=================\n【第 %d 场比赛后等级分变化】'%match_index)
        player_info_dict = player_database().get_all_info()
        for i in range(2):
            if match_info['win'] == i + 1:
                win_even_lose = 1
            elif match_info['win'] == 0:
                win_even_lose = 0.5
            else:
                win_even_lose = 0
            for player_No in match_info['team%d'%(i+1)]:
                self.calculate_one_player( match_index,player_No, win_even_lose, team_rank[i], team_rank[i-1],player_ranks_dict,player_info_dict )

    # 计算单人的ELOrank变化
    def calculate_one_player(self,match_index,player_No,win_even_lose,self_team_rank,other_team_rank,player_ranks_dict,player_info_dict ):
        """
        计算单人的ELOrank变化
        :param match_index:比赛编号
        :param player_No:玩家序号
        :param win_even_lose:胜,平,负对应1,0.5,0
        :param self_team_rank:玩家所在队伍总等级分
        :param other_team_rank:玩家对方队伍总等级分
        """
        # 在多人比赛中,D=自己分数-自己分数/己方总分*敌方总分
        player_record=self.read_player(player_No)
        player_last_rank = player_record[max(player_record.keys())]
        rank_D= player_last_rank - player_last_rank/self_team_rank * other_team_rank
        PD=1/(1+10**((-rank_D)/400))

        # 如果是定位赛，那么K是定位赛K，否则按照rank分数来
        if self.whether_init_round(player_No, player_ranks_dict):
            K=self.settings['init_round_K']
        else:
            for i in self.Ks_list:
                if player_last_rank>=i[0]:
                    K=i[1]
                    break
        printlog(player_No, win_even_lose,PD,K)
        # 最终得分 Rf=Ro+K*(W-PD)
        if self.settings["whether_int_rank"]:
            player_new_rank=round(player_last_rank+K*(win_even_lose-PD))
        else:
            player_new_rank = player_last_rank + K * (win_even_lose - PD)
        player_record[match_index]=player_new_rank
        json_write('%s/players/%d.json'%(self.match_path,player_No),player_record)
        if player_info_dict[player_No]['name']:
            printlog('%s : %d --> %d' % (player_info_dict[player_No]['name'], player_last_rank, player_new_rank))
        else:
            printlog('%s : %d --> %d' % (player_No,player_last_rank, player_new_rank))

    # 赛前信息分析
    def pre_match(self, player_No_list: list)-> list:
        """
        赛前信息分析,输入所有玩家名字,分析谁是定位赛，分差是否过大
        :param player_No_list: 数个玩家的列表
        :return: [上下分差是否超过300，定位赛玩家列表[]]
        """
        if len(self.new_match):
            printlog('比赛信息未初始化')
            return False
        result=[False,[]]
        player_ranks_dict={}
        for player_No in player_No_list:
            player_record=self.read_player(player_No)
            player_last_rank = player_record[max(player_record.keys())]
            player_ranks_dict[player_No]=player_last_rank
        for player_No in player_No_list:
            if self.whether_init_round(player_No,player_ranks_dict):
                result[1].append(player_No)
        if max(player_ranks_dict.values())-min(player_ranks_dict.values())>=300:
            result[0]=True
        return result


    # 判断是否是定位赛
    def whether_init_round(self,player_No,player_ranks_dict):
        # 总赛数少于设定次数次
        player_info = json_read('%s/players/%s.json' % (self.match_path, player_No))
        match_times=len(player_info)-1
        print('%d号数据库玩家已进行%d场比赛'%(player_No,match_times))
        if match_times>self.settings['init_round']:
            return False
        init_round_max_D=self.settings['init_round_max_D']
        others_ranks=[]
        for p,rank in player_ranks_dict.items():
            if player_No!=p:
                others_ranks.append(rank)
        average=sum(others_ranks)/len(others_ranks)
        max_rank=max(others_ranks)
        min_rank=min(others_ranks)
        for i in [average,max_rank,min_rank]:
            if player_ranks_dict[player_No]>=i+init_round_max_D or player_ranks_dict[player_No]<=i-init_round_max_D:
                print('%d号数据库玩家同他人差异超出预设，不算做定位赛'%player_No)
                return False
        print('本场比赛是%d号数据库玩家的定位赛'%player_No)
        return True

    # 读取玩家当前rank
    def read_player(self,player_No):
        if not os.path.exists('%s/players/%d.json' % (self.match_path, player_No)):
            return False
        player_record=json_read('%s/players/%d.json' % (self.match_path, player_No))
        temp={}
        for match_index,rank in player_record.items():
            temp[int(match_index)]=rank
        return temp

    # 打印所有玩家的等级分并排序
    def print_all_rank(self):
        all_player_rank_result={}
        for i in os.listdir(self.match_path+'/players'):
            player_No=int(i[:i.rfind('.')])
            player_record = self.read_player(player_No)
            player_last_rank = player_record[max(player_record.keys())]
            #print(player_No,type(player_last_rank))
            all_player_rank_result[player_No]=player_last_rank
        player_info_dict = player_database().get_all_info()
        for i in sorted(all_player_rank_result.items(),key=lambda x:x[1],reverse=True):
            player_info=player_info_dict[i[0]]
            if player_info['name']:
                print(player_info['name'],':',i[1])
            else:
                print(i[0], ':', i[1])

if __name__=='__main__':
    elo=elo_open('路人车轮').print_all_rank()
    #elo.set_Ks([[700,10],[600,15],[500,20],[350,25],[200,20],[100,15],[0,10]])
    #elo.set_init({'default_init_rank':400,'init_round':5,'init_round_K':50,'init_round_max_D':200})
    #elo.set_new_player(1,500)
    #elo.set_new_player(2,420)
    #print(elo.pre_match([1,2]))
    #elo.input_new_record({'datetime':1,'team1':[1],'team2':[2],'win':2})

