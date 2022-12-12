from lxml import etree
import urllib.request
import urllib.parse
from urllib.parse import quote,unquote


def query(content):
    content = quote(content)
    # 请求地址
    url = 'https://zh.wikipedia.org/wiki/' + content
    # 请求头部
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    }
    # 利用请求地址和请求头部构造请求对象
    req = urllib.request.Request(url=url, headers=headers, method='GET')
    # 发送请求，获得响应
    response = urllib.request.urlopen(req)
    # 读取响应，获得文本
    text = response.read().decode('utf-8')
    # 构造 _Element 对象
    html = etree.HTML(text)
    # 使用 xpath 匹配数据，得到 <div class="mw-parser-output"> 下所有的子节点对象
    x = 1
    # obj_list = html.xpath('//*[ @ id = "mw-content-text"]/div[1]/div[1]/div/div//text()')
    obj_list = html.xpath('//*[@class="thumb tright"]/div')
    captions_list = []
    for caption_list in obj_list:
        captions = caption_list.xpath('./div//text()')
        sen_list = [sen.encode('utf-8').decode() for sen_list in captions for sen in sen_list]
        sen_list_after_filter = [item.strip('\n') for item in sen_list]
        result = ''.join(sen_list_after_filter)
        captions_list.append(result)

    return captions_list

#     # 使用 xpath 匹配数据，得到 <p> 下所有的文本节点对象
#     sen_list_list = obj_list
#     # 将文本节点对象转化为字符串列表
#     sen_list = [sen.encode('utf-8').decode() for sen_list in sen_list_list for sen in sen_list]
#     # 过滤数据，去掉空白
#     sen_list_after_filter = [item.strip('\n') for item in sen_list]
#     # 将字符串列表连成字符串并返回
#     result = ''.join(sen_list_after_filter)
#     return result
#
# if __name__ == '__main__':
#     result = query('交通堵塞')
#     print(result)

