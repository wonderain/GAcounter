#import cv2
import copy
import os
import traceback
from universal import *
from window_control import *

color_points_value_list=get_global('color_points_value_list')
color_points_name_list=get_global('color_points_name_list')


#多点颜色匹配
def pic_match(img,point_list,color_list,div,ifprint=False):
    """
    多点颜色匹配
    :param img:PIL格式图像
    :param point_list:点列表
    :param color_list:点颜色列表，顺序和点对应
    :param div:容许的颜色偏差
    :param ifprint:是否打印
    :return:是否所有点都颜色匹配
    """
    for index,p in enumerate(point_list):
        for rgb,num in enumerate(img.getpixel(tuple(p))):
            if color_list[index][rgb]+div<num or color_list[index][rgb]-div>num:
                if ifprint:
                    print(color_list[index][rgb]+div,num)
                    print('颜色不匹配，%s处实际颜色为%s，应为颜色为%s'%(str(p),str(img.getpixel(tuple(p))),color_list[index]))
                return False
    return True
# 用设定内的像素点来多点匹配
def img_match(img,points_name,div=5,ifprint=False):
    #   "在房间中": [     20, 800,		1570, 120,		270, 288,   	270, 370,		1100, 114],
    #"在房间中_rgb": [	255, 255, 255,	229, 229, 229,	255, 255, 255,	255, 255, 255,	153, 153, 153],
    #print(color_points_name_list.index(points_name))
    pl = color_points_value_list[color_points_name_list.index(points_name)]
    cl = color_points_value_list[color_points_name_list.index(points_name + '_rgb')]
    point_list = [pl[i:i+2] for i in range(0,len(pl),2)]
    color_list=[cl[i:i+3] for i in range(0,len(cl),3)]
    #print(color_list)
    return pic_match(img,point_list,color_list,div,ifprint=ifprint)

# RGB像素差
def pixel_diff(img1,img2):
    """
    灰度像素差(pil)，所有像素的差异都需要减去第一个像素差
    """
    diff=0
    #start_time=time.time()
    width=min(img1.size[0],img2.size[0])
    height=min(img1.size[1],img2.size[1])
    #diff_img=Image.new('L',(width,height))
    rediff=[img2.getpixel((1,1))[rgb]-img1.getpixel((1,1))[rgb] for rgb in range(3)]
    for w in range(width):
        for h in range(height):
            for rgb in range(3):
                diff+=abs(img2.getpixel((w,h))[rgb]-img1.getpixel((w,h))[rgb]-rediff[rgb])
    #print(time.time()-start_time)
    return diff

# 返回一个灰度图像第一个黑色像素(<grey，默认为35%黑)的横纵坐标，可以用来区别那些很明显不同的图片,from_right是从右下边开始算
def first_grey(img,grey=152,from_right=False):
    if from_right:
        towards=-1
    else:
        towards = 1
    for w in range(0,towards*img.size[0],towards):
        for h in range(0,towards*img.size[1],towards):
            if img.getpixel((w,h))<=grey:
                return w,h
    return img.size

# 灰度像素差(pil)
def grey_pixel_diff(img1,img2):
    """
    灰度像素差(pil)，所有像素的差异都需要减去第一个像素差
    """
    diff=0
    #start_time=time.time()
    width=min(img1.size[0],img2.size[0])
    height=min(img1.size[1],img2.size[1])
    #diff_img=Image.new('L',(width,height))
    rediff=img2.getpixel((1,1))-img1.getpixel((1,1))
    for w in range(width):
        for h in range(height):
            diff+=abs(img2.getpixel((w,h))-img1.getpixel((w,h))-rediff)
    #print(time.time()-start_time)
    return diff

# 灰度像素差方法2（加权法）(pil)
def grey_pixel_diff2(img1,img2):
    """
    灰度像素差方法2(pil)，像素差需要除以更黑(更低值)的系数
    """
    diff=0
    width=min(img1.size[0],img2.size[0])
    height=min(img1.size[1],img2.size[1])
    for w in range(width):
        for h in range(height):
            p1=img1.getpixel((w,h))
            p2=img2.getpixel((w,h))
            diff+=abs(p2-p1)/(min([p1,p2])+1)
    return diff

def isunsame(img,i,b1):
    for j in range(img.size[1]):
        #print(img.getpixel((i,j)))
        if img.getpixel((i,j))<b1-45:
            return True
    return False
def cut_num(img):   
    b1=img.getpixel((1,1))
    cut_w=[]
    isnum=False
    for i in range(img.size[0]):
        if isunsame(img,i,b1) and not isnum:
            cut_w.append(i)
            isnum=True
        elif not isunsame(img,i,b1) and isnum:
            cut_w.append(i)
            isnum=False
    return int(len(cut_w)/2)

def wether_element_match(l1:list,l2:list,div):
    for i in range(len(l1)):
        if abs(l1[i]-l2[i])>div:
            return False
    return True
# 判断是列表中哪个图片，使用的时候要注意，返回index=0，要跟False区分
def min_diff_in_list(compare_list,img,mode=2,div=400,ifprint=False,):
    diffs = []
    max_diff=img.size[0]*img.size[1]*255 #设计的理论上最大值，当图片有明显区别时直接取这个数,一定要填充，否则最后会出错
    if mode==2:
        # img的第一个黑色像素的x位置，如果两个图片差很大(5像素)，那么一定是不同的图片，即预分析
        grey_w1,grey_h1=first_grey(img)
        #grey_w2, grey_h2 = first_grey(img,from_right=True)
        # div应当随着像素位置缩小，pre_div即是缩小后的div
        if grey_w1>=img.size[0]/2 and grey_w1<img.size[0]:
            pre_div=0.5*div
        else:
            pre_div=div * (1 - grey_w1/ img.size[0])          # 预分析的div，可以减少计算
        #print('第一黑色像素',grey_w1)
        #print(pre_div)
    else:
        pre_div = div
    for player_index,compare_img in enumerate(compare_list):
        if not compare_img:
            diffs.append(max_diff)
            continue
        if mode == 2:
            diff = grey_pixel_diff2(compare_img, img)
        elif mode==1:
            diff = grey_pixel_diff(compare_img, img)
        elif mode==3:
            diff = pixel_diff(compare_img, img)
        # 如果img的第一个黑色像素的x位置越接近中间，那么判定严格相同的标准也应该改变一下
        if diff < pre_div:
            # print(diff)
            return player_index
        diffs.append(diff)
    if div == 0 and len(diffs):
        print(diffs)
        return diffs.index(min(diffs))
    if ifprint:
        print('与各个图像的差值为:', diffs)
    return False


# 判断是哪位玩家
def which_player(player_index_imgpath_dict,img,mode=2,div:int=400,compare_img_crop=False,all_img_crop=False,grey_div=3,grey_mode=1):
    """
    那这张图片跟库图对比，判断这是哪位玩家，可以输入需要库图裁剪的尺寸
    :param grey_div: 第一黑色像素位置的可偏差值
    :param grey_mode: 第一像素位置的模式，1为xy都对比，2为仅对比x
    :param mode: 模式1是直接对比，模式2是加权对比(对黑白分明的图很有效)，模式3是彩色对比
    :param div: 容许的偏离度
    :param all_img_crop:对比图和待确定图都裁剪一部分，如果开启了这个，那么就跳过对比图裁剪
    :param player_index_imgpath_dict:玩家的序号、图片位置的字典{1:{'name':名字,'img_path':图片路径}}(名字不填也可以)
    :param img:待对比图
    :param compare_img_crop:写在字典里的库图片裁剪，默认为False，有需要则裁剪
    :return: 返回匹配图片的玩家编号或者False
    """
    if all_img_crop:
        img_ = img.crop((all_img_crop[0], all_img_crop[1], img.size[0] + all_img_crop[2], img.size[1] + all_img_crop[3]))
    else:
        img_=img
    x1, y1 = first_grey(img_)
    x2, y2 = first_grey(img_, from_right=True)
    #print(x1,y1,x2,y2)
    img_list=[]
    index_list=[]
    for player_index,info in player_index_imgpath_dict.items():
        # 如果没有info['first_grey']就会报错，但是这个其实没关系，是游戏结算的时候没有这个信息
        try:
            if grey_mode == 1 and not wether_element_match(info['first_grey'], [x1, y1, x2, y2],div=grey_div):
                continue
            elif grey_mode == 2 and not wether_element_match([info['first_grey'][0],info['first_grey'][2]], [x1, x2], div=grey_div):
                continue
        except:
            pass
        if all_img_crop:
            compare_img = Image.open(info['img_path'])
            img_list.append(compare_img.crop((all_img_crop[0], all_img_crop[1],compare_img.size[0] + all_img_crop[2],compare_img.size[1] + all_img_crop[3])))
        elif compare_img_crop:
            compare_img=Image.open(info['img_path'])
            img_list.append(compare_img.crop((compare_img_crop[0],compare_img_crop[1],compare_img.size[0]+compare_img_crop[2],compare_img.size[1]+compare_img_crop[3])))
        else:
            img_list.append(Image.open(info['img_path']))
        index_list.append(player_index)
    if len(img_list):
        result=min_diff_in_list(img_list, img_, mode=mode, div=div)
        if result is False:
            return False
        else:
            return index_list[result]
    else:
        return False
    
        
# 判断基础数字
def simple_number(img):
    path="number"
    result_dict={}
    result_list=[]
    for i in os.listdir(path):
        img2 = Image.open(path+'/'+i).convert('L')
        diff=grey_pixel_diff(img,img2)
        result_dict[i]=diff
        result_list.append(diff)
    #print(result_dict.items())
    mind=min(result_list)
    for i in result_dict:
        if result_dict[i]==mind:
            return i[:i.rfind('.')]
    
    
# 判断GA中的数字
def ga_number(img):
    try:
        number_count=cut_num(img)
        #print('数字个数：',number_count)
        start_pix=int(img.size[0]/2)-5*number_count
        result=''
        for index in range(number_count):
            im=img.crop((start_pix+index*10,0,start_pix+index*10+9,img.size[1]))
            #im.show()
            result+=simple_number(im)
        print(result)
        return int(result)
    except:
        printlog(traceback.format_exc())
        makedir('bug_img')
        img.save('bug_img/GA_number.png')
        return int(result)


# 是否两个列表里面的图片是匹配的
def whether_all_same_img(img_list1,img_list2, mode=2, div=400):
    """
    是否两个列表里面的图片是匹配的
    :param img_list1:
    :param img_list2:
    :param mode:模式1是正常对比，模式2是加权对比
    :param div:容许的偏差值
    :return:如果有任意不匹配就会返回False
    """
    img_l2=copy.deepcopy(img_list2)
    for img1 in img_list1:
        if img1:
            result=min_diff_in_list(img_l2, img1, mode=mode, div=div)
        else:
            continue
        # 两个列表中图片有任何出入
        #print(result)
        if type(result)!=type(1):
            return False
        else:
            del img_l2[result]
    return True

if __name__ =='__main__':

    '''rect, handle = get_window_pos('新热血英豪')
    Virtual_Keyboard(rect, handle).mouse_move_and_back(940, 355)
    window_image = ImageGrab.grab(rect, all_screens=True)
    now_weapon_img = window_image.crop((864, 371, 904, 411))
    now_weapon_img.show()
    result=min_diff_in_list([Image.open('weapons/%d.png'%i).convert('L') for i in range(len(os.listdir('weapons')))], now_weapon_img.convert('L'), mode=1, div = 0)
    print(result)
        '''


    # 图片测试
    '''
    path=r'F:\玩家实力评价体系\GAcount\count5\imgtest\6'
    all_img_crop=(0,3,0,-6)
    for i in os.listdir(path):
        img1 = Image.open(path + '/' + i).convert('L')
        compare_list = []
        for j in os.listdir(path):
            img2 = Image.open(path + '/' + j).convert('L')
            if i!=j:
                compare_list.append(img2.crop((all_img_crop[0], all_img_crop[1],img2.size[0] + all_img_crop[2],img2.size[1] + all_img_crop[3])))
            else:
                compare_list.append(False)
            #print(i,j,':',grey_pixel_diff2(img1,img2))
        minindex=min_diff_in_list(compare_list, img1.crop((all_img_crop[0], all_img_crop[1],img1.size[0] + all_img_crop[2],img1.size[1] + all_img_crop[3])),mode=2,div=400,ifprint=True)
        if not minindex is False:
            print('%s匹配的是%s'%(i,os.listdir(path)[minindex]))
        else:
            print('未找到除了%s自身之外的匹配图'%i)'''
    path='F:/玩家实力评价体系/GAcount/count5/路人车轮历史数据/1122-2/离线记录/5/player_database/'
    database = json_read(path+'database.json')
    for i in os.listdir(path):
        if 'png' in i:
            img=Image.open(path+i)
            x1,y1=first_grey(img.crop((0,3,img.size[0],img.size[1]-6)))
            x2,y2=first_grey(img.crop((0,3,img.size[0],img.size[1]-6)),from_right=True)
            database[i.replace('.png','')]['first_grey']=[x1,y1,x2,y2]
            print(i,x1,y1,x2,y2)
    json_write(path+'database.json',database)

