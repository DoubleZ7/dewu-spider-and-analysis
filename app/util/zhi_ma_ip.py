# coding=utf-8
import requests
from app.configUtil import ConfigUtil

config = ConfigUtil()


class ZhiMaIp:
    def __init__(self):
        self.url = config.getValue("zhi_ma_ip_url")
        self.addWhiteListIpUrl = config.getValue("white_list_ip_url")

    def getOneProxies(self):
        """
        获取一个代理服务器
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
        }
        # 检测代理活性和状态
        res = requests.get(url="http://icanhazip.com/", timeout=8, proxies=proxies)
        print(res.text)
        return proxies

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

