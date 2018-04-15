#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/2/23 16:46
# @Author  : liwenqiang
# @File    : sendpic.py

import sys
import io
import time
import urllib2
import urllib
import requests
import json
from qiniu import Auth, put_file
from qiniu import BucketManager

#自定义异常
class FError(Exception):
    def __init__(self, ErrorInfo):
        super(FError, self).__init__()
        self.errorinfo = ErrorInfo
    def __str__(self):
        return self.errorinfo

class TableauPic:
    #初始化函数
    def __init__(self,url,username,):
        self.url=url
        self.username=username
        self.server=self.get_server() #获取服务器地址
        self.target_site=self.get_target_sige() #获取站点
        self.trusted_url=self.get_trusted_url()#获取根目录
        self.view_url=self.get_view_url()#获取视图地址
        #更新数据
        self.refresh_status=self.refresh_data()

    # 获取服务器地址
    def get_server(self):
        end_index = self.url.find('/t/')
        if end_index == -1:
            end_index = self.url.find('/views/')
        return self.url[0:end_index + 1]
    # 需要向这个地址post数据
    def get_trusted_url(self):
        return self.get_server() + 'trusted/'
    # 获取站点
    def get_target_sige(self):
        start_index = self.url.find('/t/')
        if start_index==-1:
            return 'default'
        else:
            end_index = self.url.find('/views/')
            return self.url[start_index+3:end_index]
    #获取视图地址
    def get_view_url(self):
        start_index = self.url.find('/views/')
        end_index = self.url.find('?:')
        return self.url[start_index:end_index]
    # 获取ticket
    def get_ticket(self):
        headers = {'UserAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0',
                   'Referer': 'http://tableau.ai.babytree/'}

        if self.target_site=='default':
            values = {'username': self.username}
        else:
            values = {'username': self.username, 'target_site': self.target_site}
        data = urllib.urlencode(values)
        s = urllib2.Request(self.trusted_url, headers=headers, data=data)
        try:
            response = urllib2.urlopen(s)
            ticket = response.read()
            if len(ticket) > 300:
                return 'err'
            return ticket
        except:
            return 'err'
    # 获取图片链接
    def get_pic_url(self,ticket):
        if self.target_site=='default':
            new_url = self.trusted_url + ticket + self.view_url + '?:format=png&:refresh=yes'
        else:
            new_url = self.trusted_url + ticket +'/t/'+self.target_site+self.view_url  + '?:format=png&:refresh=yes'
        return new_url
    # 第一次链接，以刷新数据
    def refresh_data(self):
        ticket=self.get_ticket()
        pic_url=self.get_pic_url(ticket)
        try:
            r=requests.get(pic_url)
            if r.status_code==200:
                time.sleep(15)
                return True
            else:
                return False
        except:
            return False

    # 保存图片
    def save_pic(self,pic_url, filepath):
        img = requests.get(pic_url)
        f = open(filepath, 'wb')  # 存储图片，多媒体文件需要参数b（二进制文件）
        f.write(img.content)  # 多媒体存储content
        f.close()
        return True

#向钉钉群发消息
class ToDingDing():
    def __init__(self,dd_url):
        self.dd_url=dd_url

    def send_mkd(self,title,text,pic_url):
        title=title
        text=text
        pic_url=pic_url
        content = {"msgtype": "markdown",
                   "markdown": {"title": "%s" % (title),
                                "text": "#### %s\n" % (text) +
                                        ">![总体](%s)\n" % (pic_url)
                                }
                   }
        data = json.dumps(content).encode('UTF-8')
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        s = urllib2.Request(self.dd_url, headers=headers, data=data)
        urllib2.urlopen(s)

# 上传文件到云端，返回超链接，这里有两种方法，一种是贴图库的服务
# 一种是七牛云的服务，文件的配置内容都写写死了
class PicUp():
    def __init__(self,tietu_config,qiniu_config):
        self.tietu_config=tietu_config
        self.qiniu_config=qiniu_config

    def getTieTuUrl(self, file_path):
        # 使用贴图库的服务
        up_url = self.tietu_config['up_url']
        # 相册的token
        token = self.tietu_config['token']
        # 相册ID
        aid = self.tietu_config['aid']
        keywords = {'Token': token,
                    'from': 'file',
                    'aid': aid
                    }
        pic = {'file': open(file_path, 'rb')}
        r = requests.post(up_url, data=keywords, files=pic)
        js=json.loads(r.text)
        try:
            pic_url=js['linkurl'].encode('utf-8')
        except:
            pic_url='tietu_err'
        return pic_url


    def getQiniuUrl(self,file_path,file_name):
        access_key = self.qiniu_config['access_key']
        secret_key = self.qiniu_config['secret_key']
        bucket_name =self.qiniu_config['bucket_name']
        bucket_url = self.qiniu_config['bucket_url']

        try:
            q = Auth(access_key, secret_key)
            # 上传
            token = q.upload_token(bucket_name, file_name, 3600)
            info = put_file(token, file_name, file_path)
            if info[1].status_code==200:
                img_url = '%s/%s' % (bucket_url, file_name)
            else:
                img_url = 'qiniu_err'
        except:
            img_url='qiniu_err'
        return img_url

def send_msg(title,text):
    dd_url="https://oapi.dingtalk.com/robot/send?access_token=b4b76b6690fadf24dfadggg232b41244871e3c5bfacdd37cf2994ac71a587912692"
    title = title.decode("utf-8")
    text =  text.decode("utf-8")

    print type(title)
    content = {
			 "msgtype": "markdown",
			 "markdown": {
				 "title":u"发送钉钉ERROR",
				 "text":u"%s\n"%(title) +"> ###### %s\n"%(text)
			 } ,
			 "at": {"isAtAll": 'false'}
			 }
    data = json.dumps(content).encode('UTF-8')
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    s = urllib2.Request(dd_url, headers=headers, data=data)
    urllib2.urlopen(s)

if __name__=='__main__':
    ######全局变量，需要设置
    sys_path = sys.path[0]+'/img_log'
    now_time = time.strftime('%m%d%H%M%S', time.localtime(time.time())) #当前时间
    root_path = sys_path#文件根路径
    file_name='/'+sys.argv[1]+now_time+'.png'  #文件名称
    file_path=root_path+file_name  #文件路径
    title = sys.argv[4] #报表需求的标题
    ######tableau部分的内容,如果报错会发消息给测试群
    url = sys.argv[2]
    username = 'web_admin'
    try:
        tb = TableauPic(url, username)
        if not tb.refresh_status:
            raise FError('tableau报表地址错误')
        tb_ticket = tb.get_ticket()
        if tb_ticket=='-1':
            raise FError('票证获取异常，为-1')
        if tb_ticket=='err':
            raise FError('票证获取异常')
        print '获取票证成功'
        tab_pic_url = tb.get_pic_url(tb_ticket)

        print '生成链接为:'+tab_pic_url
        savepic_flag=tb.save_pic(tab_pic_url, file_path)
        if not savepic_flag:
            raise FError('生成图片失败')
        print '生成图片成功'
    except FError as e:
        print e.errorinfo
        send_msg(title,e.errorinfo)
        exit()
    ###上传图片部分 ，上传到云端，并获取图片超链接
    # #这里配置 贴图网的信息
    tietu_config={'up_url':'http://up.imgapi.com/', #api地址
                  #token
                  'token':'b37e60452a39ae45c5ef1f3c3c8da2d8d4598a40:pfas44edibRYZQywCqf4XOn4WwM=:eyJkZWdfa44Fk44fdMTUyMzQyODdgiYWN0aWd4iZ2V0IiwdfaidEEdIjoiNjQdf2IxIiwiYddfaTQyOTU2MCIsImZyb20iOiJmaWxlIn0=',
                  'aid':75823289 #相册ID
                  }
    #这里配置 七牛云的信息
    qiniu_config={'access_key':'VxZQdrx44dsa2KwWrfadFhp4EMdfa4d212zQ5JoprbiGrCgn5T0RPvr9zv',
                  'secret_key':'UFPjJ5EGz071i3234f23BmeLMTddBN5EcIKKEbspH1dnLafhn',
                  'bucket_name':'fspy',# 填入你的七牛空间名称
                  'bucket_url':'http://ulDkjtll682.bkt.clouddn.com' # 填入你的域名地址，主要是为了记录图片上传后的地址
                   }
    pu = PicUp(tietu_config,qiniu_config) # 初始化，需要用哪个服务则初始化好这个，并选用对应的函数即可
    try:
        # pic_link_url=pu.getTieTuUrl(file_path)
        pic_link_url=pu.getQiniuUrl(file_path,file_name)

        if pic_link_url=='tietu_err':
            raise FError('照片上传到贴图服务错误')
        if pic_link_url=='qiniu_err':
            raise FError('照片上传到七牛云服务错误')
        print pic_link_url
    except FError as e:
        print e.errorinfo
        send_msg(title, e.errorinfo)
        exit()
    # # # # 钉钉机器人发送到钉钉群
    dingding_url = sys.argv[3]
    # dingding_url = "https://oapi.dingtalk.com/robot/send?access_token=b4b76fasffa4sa33b6d690275e4b2424871e3c5bf4dac37cf2994ac71a587912692"  # 测试群
    # #dingding_url='https://oapi.dingtalk.com/robot/send?access_token=ceb8fdaf10b8069e81341e5fcdfa3bdsf5fhdf07d76b25b9846bd52f34fcf329ff806'#正式群
    dd = ToDingDing(dd_url=dingding_url)
    text = sys.argv[5]
    dd.send_mkd(title=title, text=text, pic_url=pic_link_url)
    print '发送成功'