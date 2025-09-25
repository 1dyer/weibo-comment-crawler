import requests
import json
from datetime import datetime
import csv
import time

# 统计评论数量
count=0
def add_count():
    global count
    count +=1

# 获取标头
def get_header():
    with open("weibo_cookie.json",'r') as f:
        header=json.loads(f.read())
        # 加上Referer
        header['referer']='https://weibo.com/'
    return header

# 提取url中的关键词
def get_keyword(url):
    list = url.split('/')
    return list[-2],url_to_mid(list[-1])

# 解码
def decode_base62(b62_str):
    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = 62
    num = 0
    for c in b62_str:
        num = num * base + charset.index(c)
    return num
def url_to_mid(url):
    result = ''
    for i in range(len(url), 0, -4):
        start = max(i - 4, 0)
        segment = url[start:i]
        num = str(decode_base62(segment))
        if start != 0:
            num = num.zfill(7)  # 除最后一段外都补满7位
        result = num + result
    return int(result)

# 根据UID返回博主的用户名
def get_name(uid):
    url = f"https://weibo.com/ajax/profile/info?custom={uid}"
    return json.loads(requests.get(url=url,headers=get_header()).content.decode('utf-8'))['data']['user']['screen_name']

# 计算年龄
def get_age(birthday):
    birth = datetime.strptime(birthday, "%Y-%m-%d")
    today = datetime.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

# 返回用户数据
def get_user_info(uid):
    # 第一部分信息
    url = f"https://weibo.com/ajax/profile/info?uid={uid}"
    data = json.loads(requests.get(url=url,headers=get_header()).content.decode('utf-8'))['data']['user']
    # 粉丝
    followers_count = data['followers_count']
    # 关注
    friends_count = data['friends_count']
    # 转赞评
    try:
        total_cnt = data['status_total_counter']['total_cnt']
        total_cnt = int(total_cnt.replace(",", ""))
    except:
        total_cnt = ''
    # 简介
    try:
        description = data['description']
    except:
        description = ''
    # 是否认证
    if data['verified'] == True:
        verified = '是'
    else:
        verified = '否'
    # 性别
    try:
        gender = data['gender']
        if gender == 'm':
            gender = '男'
        elif gender == 'f':
            gender = '女'
        else:
            gender = '未知'
    except:
        gender = '未知'
    # 会员等级
    try:
        svip = data['svip']
    except:
        svip = ''
    
    # 第二部分信息
    url = f"https://weibo.com/ajax/profile/detail?uid={uid}"
    data = json.loads(requests.get(url=url,headers=get_header()).content.decode('utf-8'))['data']
    # 年龄
    try:
        age = data['birthday'].split(' ')[0]
        age = get_age(age)
    except:
        age = ''
    # 星座
    try:
        constellation = data['birthday'].split(' ')[1]
    except:
        constellation = ''

    # 微博注册日期
    try:
        weibo_created =  data['created_at']
    except:
        weibo_created = ''
    # 学校
    try:
        school = data['education']['school']
    except:
        school = ''
    # 公司
    try:
        career = data['career']['company']
    except:
        career = ''
    # 微博认证
    try:
        desc_text = data['desc_text']
    except:
        desc_text = ''
    # 主页IP
    try:
        user_location = data['ip_location'][5:]
    except:
        user_location = '其他'
    # 信用
    try:
        sunshine_credit = data['sunshine_credit']['level'][2:]
    except:
        sunshine_credit =''

    
    return followers_count,friends_count,total_cnt,user_location,description,verified,gender,svip,age,constellation,weibo_created,school,career,desc_text,sunshine_credit



# 返回评论数据
def get_data(data):
    # 评论ID
    idstr = data['idstr']
    # 上级评论ID
    rootidstr = data['rootidstr']
    # 发表日期
    created_at = data['created_at']
    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
    # 用户名
    screen_name = data['user']['screen_name']
    # 用户ID
    user_id = data['user']['id']
    # 评论内容
    text_raw = data['text_raw']
    # 评论点赞数
    like = data['like_counts']
    # 评论回复数量
    try:
        total_number = data['total_number']
    except:
        total_number = 0
    # 评论IP
    com_source = data['source'][2:]
    # 粉丝等级
    fan={
        '1':'铁粉',
        '2':'金粉',
        '3':'钻粉'
    }
    try:
        icon_url = data['user']['fansIcon']['icon_url']
        fansIcon = f"{fan[icon_url[-7]]}{icon_url[-5]}"
    except:
        fansIcon = ''
    # 获取用户信息
    followers_count,friends_count,total_cnt,user_location,description,verified,gender,svip,age,constellation,weibo_created,school,career,desc_text,sunshine_credit = get_user_info(user_id)
    

    return idstr,created_at,screen_name,user_id,text_raw,like,com_source,total_number,rootidstr,fansIcon,followers_count,friends_count,total_cnt,user_location,description,verified,gender,svip,age,constellation,weibo_created,school,career,desc_text,sunshine_credit
           

# 获取全部信息
def get_information(uid,mid,max_id,fetch_level):
    if max_id == '':
        url = f"https://weibo.com/ajax/statuses/buildComments?flow=1&is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&count=20&uid={uid}&fetch_level={fetch_level}&locale=zh-CN"
    else:
        url = f"https://weibo.com/ajax/statuses/buildComments?flow=1&is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&max_id={max_id}&count=20&uid={uid}&fetch_level={fetch_level}&locale=zh-CN"

    resp = json.loads(requests.get(url=url,headers=get_header()).content.decode('utf-8'))
    datas = resp['data']

    for data in datas:
        add_count()
        idstr,created_at,screen_name,user_id,text_raw,like,com_source,total_number,rootidstr,fansIcon,followers_count,friends_count,total_cnt,user_location,description,verified,gender,svip,age,constellation,weibo_created,school,career,desc_text,sunshine_credit = get_data(data)
        if fetch_level == 0:
            rootidstr = ''
        csv_writer.writerow([count,idstr,rootidstr,user_id,created_at,screen_name,gender,text_raw,like,total_number,fansIcon,com_source,user_location,description,desc_text,verified,svip,age,constellation,school,career,weibo_created,sunshine_credit,followers_count,friends_count,total_cnt])
        time.sleep(0.5)
        # 判断是否存在二级评论
        if total_number >0 and fetch_level == 0:
            get_information(uid,idstr,0,1)
    print(f"当前爬取:{count}条")

    
    # 下一条索引
    max_id = resp['max_id']
    if max_id != 0:    
        get_information(uid,mid,max_id,fetch_level)
    else:
        return
    
    

if __name__ == "__main__":


    # 统计爬虫运行时间
    start = time.time()

    # 所要爬取的页面地址
    url = "https://weibo.com/6593199887/PjoY682IF"


    uid,mid=get_keyword(url)
    print(f"\n创建csv表中...\n创建  {get_name(uid)}_{url.split('/')[-1]}_评论(Max版)  ....")

    # 创建CSV文件并写入表头
    with open(f'./MaxData/{get_name(uid)}_{url.split('/')[-1]}_评论(Max版).csv', mode='w', newline='', encoding='utf-8-sig') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['序号','评论标识号','上级评论','用户标识符','时间','用户名','性别','评论内容','评论点赞数','评论回复数','粉丝牌','评论IP','主页IP','用户简介','微博认证','是否认证','会员等级','年龄','星座','学历','公司','微博注册日期','信用','用户粉丝数','用户关注数','用户转赞评数'])
        get_information(uid,mid,'',0)

    
    print(f"评论爬取完成，共计{count}条，耗时{(time.time()-start)/60:.2f}分")
