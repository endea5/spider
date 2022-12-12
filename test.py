import threading
import requests
import re
import time
from urllib.parse import quote,unquote
from get_token import query
from ippool import get_proxy
from lxml import etree
import zhconv

g_mutex = threading.Condition()
g_pages = []  # 储存广度爬虫获取的html代码，之后解析所有url链接
g_queueURL = []  # 等待爬取的url链接列表
g_existURL = []  # 已经爬取过的url链接列表
g_writecount = 0  # 找到的链接数

requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
requests.session().keep_alive = False


class Crawler:
    def __init__(self, url, threadnum):
        self.url = url
        self.threadnum = threadnum
        self.threadpool = []

    def craw(self):  # 爬虫的控制大脑，包括爬取网页，更新队列
        global g_queueURL
        g_queueURL.append(url)
        depth = 1
        while depth < 8:
            print('Searching depth ', depth, '...\n')
            self.downloadAll()
            self.updateQueueURL()
            g_pages = []
            depth += 1

    def downloadAll(self):  # 调用多线程爬虫，在小于线程最大值和没爬完队列之前，会增加线程
        global g_queueURL
        i = 0
        while i < len(g_queueURL):
            j = 0
            while j < self.threadnum and i + j < len(g_queueURL):
                threadresult = self.download(g_queueURL[i + j], j)
                j += 1
            i += j
            for thread in self.threadpool:
                thread.join(30)
            threadpool=[]
        g_queueURL=[]

    def download(self, url, tid):  # 调用多线程爬虫
        crawthread=CrawlerThread(url, tid)
        self.threadpool.append(crawthread)
        crawthread.start()

    def updateQueueURL(self):  # 完成一个深度的爬虫之后，更新队列
        global g_queueURL
        global g_existURL
        newUrlList = []
        for content in g_pages:
            newUrlList += self.getUrl(content)
        g_queueURL=list(set(newUrlList)-set(g_existURL))

    def getUrl(self, content):  # 从获取的网页中解析url
        link_list = re.findall('<a href="/wiki/(Category:.*?)" title="Category.*?</a>', content)
        unique_list = list(set(link_list))
        return unique_list


class CrawlerThread(threading.Thread):  # 爬虫线程
    def __init__(self, url, tid):
        threading.Thread.__init__(self)
        self.url=url
        self.tid=tid

    def run(self):
        global g_mutex
        global g_writecount
        try:
            print (self.tid, "crawl ", unquote(self.url))
            headers = {'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}

            proxy = get_proxy().get("proxy")

            r = requests.get("https://zh.wikipedia.org/wiki/" + self.url, headers=headers, proxies={"http": "http://{}".format(proxy)})
            html = r.text

            # print(proxy)

            # link_list2 = re.findall('<a href="/wiki/(Category:.*?)" title="Category.*?</a>', html)
            # unique_list2 = list(set(link_list2))
            # for eachone in unique_list2:
            #     g_writecount += 1
            #     content2 = "No." + str(g_writecount) + "\t Thread" + str(self.tid) + "\t" + unquote(self.url) + '->' + unquote(eachone) + '\n'
            #     with open('title.txt', "a+") as f:  # 将网页内容写道title.txt
            #         f.write(content2)


            link_list3 = re.findall('<li><a href="/wiki/(%.*?)".*?</li>', html)
            if len(link_list3) != 0:
                unique_list3 = list(set(link_list3))
                for eachimage in unique_list3:
                    img_data = requests.get('https://zh.wikipedia.org/wiki/' + eachimage, headers=headers, proxies={"http": "http://{}".format(proxy)})
                    image_page = img_data.text


                    img_content = img_data.content
                    img_html = etree.HTML(img_content)
                    image_src_list = img_html.xpath('//*[@class="thumb tright"]/div/a/img/@src')
                    image_name_list = re.findall('<a href="/wiki/File:(.*?).jpg" class="image">', image_page)
                    if len(image_src_list) == 0:
                        break
                    captions_list = query(unquote(eachimage))

                    if len(captions_list) == len(image_src_list):
                        for i in range(len(captions_list)):
                            image = requests.get(url='https:' + image_src_list[i], headers=headers, proxies={"http": "http://{}".format(proxy)}).content
                            f1 = open('D:/data/' + unquote(image_name_list[i]) + '.jpg', 'wb')
                            f1.write(image)
                            f1.close()
                            f2 = open('D:/data/11111.txt', 'a+')
                            f2.write('{\nname:' + zhconv.convert(unquote(image_name_list[i]), 'zh-cn') + '.jpg' + '\ntag:' + zhconv.convert(unquote(eachimage), 'zh-cn') + '\ncaptions:' + zhconv.convert(unquote(captions_list[i]), 'zh-cn') + '\nurl:https://zh.wikipedia.org/wiki/' + unquote(eachimage) + '\n},\n')
                            f2.close()

                            # with open('D:/data/' + unquote(image_name_list[i]) + '.jpg', 'wb') as fi:
                            #     fi.write(image_src_list[i])
                            # with open('D:/data/11111.txt', "a+") as ft:
                            #     ft.write('{\nname:' + unquote(image_name_list[i]) + '\ntag:' + eachimage + '\ncaptions:' + unquote(captions_list[i]) + '\nurl:https://zh.wikipedia.org/wiki/' + eachimage + '\n},')

        except Exception as e:
            g_mutex.acquire()
            g_existURL.append(self.url)
            g_mutex.release()
            print('Failed downloading and saving',self.url)
            print(e)
            return None
        g_mutex.acquire()
        g_pages.append(html)
        g_existURL.append(self.url)
        g_mutex.release()


if __name__ == "__main__":
    url = "Wikipedia:%E5%88%86%E7%B1%BB%E7%B4%A2%E5%BC%95"
    threadnum = 10
    crawler = Crawler(url,threadnum)
    crawler.craw()
