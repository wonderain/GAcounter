import time

from universal import  *
from img_deal import  *


class player_database():
    def __init__(self,img_type=''):
        """
        记录所有对战截图过的玩家的记录序号No、name和截图(截图名即是序号No)和可能的玩家昵称
        功能是：
        1、搜索数据库中图片（结算界面），若没有匹配的对象，则将图像按编号保存
        2、room模式的图片偏差应该在700以内，结算界面模式在500以内
        3、手动记录图片对应的名字
        {1:{‘name’:宇宙大王,'user':[宇宙大王]},2:{'name':'乏善可陈','user':[闹过，义山]}}
        仅接受PIL格式的图片
        :param img_type:名字图片类型，分为在房间里的名字(room)和结算时的名字(默认)两类
        """
        if not os.path.exists('player_database'):
            os.mkdir('player_database/')
            json_write('player_database/database.json',{})
        self.img_type=img_type

    # 设定一个新玩家记录
    def new_player(self,img,database):
        """
        设定一个新玩家记录，需要注意的是，json会将Int键转化为字符串，读取的时候需要转换回来
        :param img:
        :param database:
        :return:
        """
        player_No=len(database)+1
        save_path='player_database/%d.png'%player_No
        imgc=img.crop((0, 3, img.size[0] , img.size[1]-6))
        x1, y1 = first_grey(imgc)
        x2, y2 = first_grey(imgc, from_right=True)
        database[str(player_No)]= {'No':player_No,'name':False,'user':[],'img_path':save_path,'first_grey':[x1,y1,x2,y2]}
        img.save(save_path)
        json_write('player_database/database.json',database)
        return database[str(player_No)]

    # 根据图片和模式搜索对应的玩家database,默认自动记录新玩家
    def which_player_in_database(self,img,savenew=True):
        """
        根据图片和模式搜索对应的玩家database
        :param img:用于搜索的图片
        :return:搜索到则返回信息，未搜索到且图片是结算模式则新建数据，未搜索到且是room模式则返回False
        """
        database=json_read('player_database/database.json')
        start_time=time.time()
        if self.img_type=='room':
            No=which_player(database,img,div=600,compare_img_crop=(0, 6,0, - 11),grey_div=5,grey_mode=2)
        else:
            No = which_player(database,img, div=400,all_img_crop=(0,3,0,-6),grey_div=3,grey_mode=2)
        print('本次玩家数据库搜索花费%.1f秒,结果为:%s'%(time.time()-start_time,str(No)))
        if not No is False:
            return database[str(No)]# 加1是因为which_player函数起始是0
        if self.img_type!='room' and savenew:   #如果不是room模式，也就是说是结算界面模式，则记录新玩家
            return self.new_player(img,database)
        return False

    def get_all_unnamed_No(self):
        database = json_read('player_database/database.json')
        result=[]
        for No,info in database.items():
            if not info['name']:
                result.append(int(No))
        return result

    def set_No_name(self,No,name):
        database = json_read('player_database/database.json')
        database[str(No)]['name']=name
        json_write('player_database/database.json', database)

    def get_No_name(self,No):
        database = json_read('player_database/database.json')
        #print(No, database)
        return database[str(No)]['name']

    # 获得所有数据，注意将str的序号No转成int
    def get_all_info(self):
        database = json_read('player_database/database.json')
        result={}
        for No_str,info in database.items():
            result[int(No_str)]=info
        return result

if __name__=='__main__':
    # 查重
    for i in os.listdir('player_database'):
        if '.png' in i:
            img1 = Image.open('player_database/' + i)
            print(i,end=':')
            mind=99999
            for j in os.listdir('player_database'):
                if '.png' in j:
                    img2 = Image.open('player_database/' + j)
                    diff=grey_pixel_diff2(img1,img2)
                    if diff<500:
                        print(j,end=' ')
                    if diff>500 and diff<mind:
                        mind=diff
            print('mind:',mind)