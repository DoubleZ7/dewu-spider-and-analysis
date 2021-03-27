# coding=utf-8
import requests
import time
from app.configUtil import ConfigUtil

config = ConfigUtil()


class ZhiMaIp:
    def __init__(self):
        self.url = config.getValue("zhi_ma_ip_url")
        self.addWhiteListIpUrl = config.getValue("white_list_ip_url")

    def send_request(self):
        """
        发送请求获取一个代理
        :return:
        """
        res = requests.get(self.url)
        hostAndPort = res.text
        hostAndPort = hostAndPort.replace('\n', '').replace('\r', '')
        if len(hostAndPort) > 30:
            self.addWhiteList()
            res = requests.get(self.url)
            hostAndPort = res.text
            hostAndPort = hostAndPort.replace('\n', '').replace('\r', '')
        proxyMeta = "http://%(proxies)s" % {
            "proxies": hostAndPort
        }

        proxies = {
            "https": proxyMeta,
            "http": proxyMeta
        }
        return proxies

    def getOneProxies(self):
        """
        获取一个代理服务器
        :return:
        """
        while True:
            proxies = self.send_request()
            res = self.check_proxies(proxies)
            if res:
                break
        return proxies

    @staticmethod
    def check_proxies(proxies):
        """
        检测代理活性和状态
        :param proxies:
        :return:
        """
        # 检测代理活性和状态
        start = time.clock()
        res = requests.get(url="http://icanhazip.com/", timeout=8, proxies=proxies).text.replace('\n', '')
        end = time.clock()
        return (end - start) < 2 and res in str(proxies)

    def addWhiteList(self):
        """
        添加一个IP至白名单
        :return:
        """
        ip = requests.get(url="http://ip.42.pl/raw").text
        url = self.addWhiteListIpUrl + ip
        requests.get(url)


if __name__ == '__main__':
    z = ZhiMaIp()
    print(z.getOneProxies())

