#!/bin/sh
. /etc/profile
. ~/.bash_profile
. ~/.bashrc

export LANG=zh_CN.UTF-8/
send_pic='/opt/project/sys/py_script/send_pic.py'

if test $# -ge 1
then 
begin=`date -d "$1 -1days" "+%Y-%m-%d"`
else
begin=`date -d -1days +%Y-%m-%d`
fi



cd /opt/project/tst/liwenqiang    

echo "Running Start:"`date -d 0days "+%Y-%m-%d %H:%M:%S"`

filename='test'
tableau_url="http://10.1.5.94/t/portal/views/GMV/GMV_1?:embed=y&:showShareOptions=true&:display_count=no&:showVizHome=no"
dingding_url='https://oapi.dingtalk.com/robot/send?access_token=b4b76b66902b41246a8de575e4b2424871e3c5bfac37cf2994ac71a587912692'
title='中文标题'
text='中文文本'

echo  $filename
echo  $tableau_url 
echo  $dingding_url
echo  $title
echo  $text

python $send_pic  $filename $tableau_url $dingding_url $title $text
if test $? -ne 0
then
exit 11
fi