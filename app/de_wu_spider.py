import requests
import time
import os
import datetime
import random

from app.util import request_util
from app.db.my_sql_db import mysqlDb
from app.configUtil import ConfigUtil
from app.util.zhi_ma_ip import ZhiMaIp
from app.log import Logger


class DeWuSpider:
    def __init__(self):
        self.db = mysqlDb()
        self.config = ConfigUtil()
        self.log = Logger().logger
        self.zm = ZhiMaIp()
        self.proxies = self.zm.getOneProxies()

        # 移除跳过认证警告
        requests.packages.urllib3.disable_warnings()

    def get_info(self, spuId):
        """
        根据spuId获取商品信息
        :param spuId:得物唯一标识
        :return:
        """
        self.log.info(f"开始获取详情-->spuId:{spuId}...")
        data = {
            "spuId": spuId,
            "productSourceName": "",
            "propertyValueId": "0"
        }
        data = request_util.add_sign(data)
        url = 'https://app.dewu.com/api/v1/h5/index/fire/flow/product/detail'
        # 发送请求
        res = self.try_err_send_request('info', data, url)
        if res.status_code == 200:
            self.log.info(f"spuId:{spuId},发送请求成功，正在解析数据...")
            data = res.json().get('data')
            # 详情
            pageDetail = data.get('detail')
            articleNumber = pageDetail.get('articleNumber')
            detail = self.db.getOne("SELECT * FROM org_detail WHERE article_number = '{}'".format(articleNumber))
            if not detail:
                # 参数
                baseProperties = data.get('baseProperties')
                brandList = baseProperties["brandList"]
                parameterList = baseProperties["list"]
                parameters = self.get_parameter(parameterList)

                # 图片
                image_and_txt = data.get("imageAndText")
                imgList = self.get_img_url(image_and_txt, articleNumber)

                # 下载logo
                logoUrl = self.downloadImg(pageDetail["logoUrl"], articleNumber)
                detail = (
                    None,
                    pageDetail.get('title'),
                    spuId,
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    pageDetail.get('authPrice'),
                    pageDetail.get('sellDate'),
                    articleNumber,
                    logoUrl,
                    brandList[0].get("brandName"),
                    parameters["functionality"],
                    parameters["blendent"],
                    parameters["upperLevel"],
                    parameters["topShoeStyles"],
                    parameters["heelType"],
                    None
                )
                self.log.info(f"spuId:{spuId},开始入库...")
                # 持久化到数据库
                # 插入详情
                detail_sql = 'INSERT INTO org_detail VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                self.db.insertData(detail_sql, detail)
                # 插入详情图片
                insert_img_sql = 'INSERT INTO org_detail_img VALUES(%s, %s, %s, %s, %s, %s)'
                self.db.insertDataList(insert_img_sql, imgList)
                self.log.info(f"spuId:{spuId},入库结束...")

    @staticmethod
    def get_parameter(parameterList):
        """
            根据参数列表返回参数字典
            :param parameterList: 参数列表
            :return:参数字典
        """
        parameter = {'functionality': None, 'blendent': None, 'upperLevel': None, 'topShoeStyles': None, 'heelType': None}
        for p in parameterList:
            key = p['key']
            value = p['value']
            if key == '功能性':
                parameter['functionality'] = value
            elif key == '配色':
                parameter['blendent'] = value
            elif key == '鞋帮高度':
                parameter['upperLevel'] = value
            elif key == '鞋头款式':
                parameter['topShoeStyles'] = value
            elif key == '鞋跟类型':
                parameter['heelType'] = value
        return parameter

    def get_img_url(self, images, article_number):
        """
        获取图片URL
        :param article_number:
        :param images:
        :return:
        """
        imgList = []
        count = 1
        for g in images:
            if len(g) > 2:
                # 判断是否为尺码对照表
                contentType = g['contentType']
                if contentType != 'STRUCTURE_SIZE' and contentType != 'SIZETEMPLATE' and contentType != 'ATTENTION':
                    g = g['images'][0]
                else:
                    continue
                u = self.downloadImg(g.get('url'), article_number + str(count))
                height = g["height"]
                if height > 100:
                    img = (
                        None,
                        article_number,
                        u,
                        count,
                        g["width"],
                        g["height"]
                    )
                    imgList.append(img)
                    count += 1
        return imgList

    def get_record(self, spuId):
        """
        获取当天的交易记录
        :param spuId: 得物唯一标识
        :return:
        """
        self.log.info(f"开始获取交易记录-->spuId:{spuId}...")
        # 获取当前商品的货号
        get_article_number_sql = f"SELECT article_number FROM org_detail WHERE spu_id = '{spuId}'"
        _article_number = self.db.getOne(get_article_number_sql)[0]

        # 获取最新一条交易记录
        get_newest_sql = f"select * from org_last_record r WHERE article_number='{_article_number}'"
        newest = self.db.getOne(get_newest_sql)
        lastId = ""
        count = 1
        while True:
            self.log.info(f"正在请求{spuId}---第{count}页---交易记录...")
            record, lastId, flag_stop = self.get_trading_record(spuId, lastId, _article_number, newest)
            # 插入数据库
            insert_sql = 'INSERT INTO org_purchase_record VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
            self.log.info(f"spuId：{spuId}---第{count}页---交易记录解析完成")
            self.db.insertDataList(insert_sql, record)
            # 判断当前是否为第一次获取
            if count == 1 and len(record) > 0:
                # 删除上次获取的记录
                del_sql = f"DELETE FROM org_last_record WHERE article_number = '{_article_number}'"
                self.db.executeSql(del_sql)
                # 把当前最新的记录更新到列表
                insert_sql = 'INSERT INTO org_last_record VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                self.db.insertData(insert_sql, record[-1])

            # 判断是否停止
            if flag_stop:
                self.log.info(f"spuId：{spuId}---今日交易记录获取完成")
                break

            # 随机随眠一到三秒
            time.sleep(random.randint(1, 3))
            count += 1

    def get_trading_record(self, spuId, lastId, _article_number, newest):
        """
        根据spuId获取交易记录
        :param newest: 最新交易记录
        :param _article_number:货号
        :param spuId: 得物唯一标识
        :param lastId: 下一页标识
        :return:返回交易记录和下一页标识
        """
        recordList = []
        # 标识是否还要继续爬取
        flag_stop = False
        data = {
            "spuId": spuId,
            "limit": '20',
            "lastId": lastId,
            "sourceApp": "app"
        }
        data = request_util.add_sign(data)
        url = 'https://app.dewu.com/api/v1/h5/commodity/fire/last-sold-list'
        # 发送请求
        res = self.try_err_send_request('record', data, url)
        if res.status_code == 200:
            all_data = res.json()
            lastId = all_data.get('data').get('lastId')
            # 判断下一次请求是否已经无数据，如果是返回空集合与停止循环标识
            if lastId == "":
                flag_stop = True
                return recordList, lastId, flag_stop

            data_list = all_data.get('data').get('list')
            for d in data_list:
                formatTime = d['formatTime']
                formatTime = self.refactorFormatTime(formatTime)
                record = (
                    None,
                    spuId,
                    _article_number,
                    d['userName'],
                    formatTime,
                    d['price'] / 100,
                    d['orderSubTypeName'],
                    d['propertiesValues'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                )

                # 判断是否是当天的数据 如果是则放入集合，如果不是则跳出循环标识不再获取交易记录
                if newest:
                    if self.compareRecord(newest, record):
                        flag_stop = True
                        break

                recordList.append(record)
        return recordList[::-1], lastId, flag_stop

    @staticmethod
    def compareRecord(dbData, record):
        """
        比较两条记录是否相等
        :param dbData:
        :param record:
        :return:
        """
        for i in range(len(record)):
            if i == 0 or i == 4 or i == 8:
                continue
            if i == 5:
                price = dbData[i]
                if not int(price) == record[i]:
                    return False
            else:
                if not dbData[i] == record[i]:
                    return False
        return True

    @staticmethod
    def refactorFormatTime(formatTime):
        """
        重构交易时间返回数据类型yyyy-MM-dd
        :param formatTime:
        :return:
        """
        if '前' in formatTime or '刚刚' == formatTime:
            if '小时' in formatTime:
                h = formatTime[0:formatTime.find('小')]
                newTime = (datetime.datetime.now() + datetime.timedelta(hours=-int(h))).strftime("%Y-%m-%d")
            else:
                newTime = datetime.datetime.now().strftime("%Y-%m-%d")
            if '天' in formatTime:
                dd = formatTime[0:formatTime.find('天')]
                newTime = (datetime.datetime.now() + datetime.timedelta(days=-int(dd))).strftime("%Y-%m-%d")
        else:
            if '月' in formatTime:
                newTime = time.strftime("%Y", time.localtime()) + '-' + formatTime.replace('月', '-').replace('日', '')
            else:
                newTime = formatTime.replace('.', '-')
        return newTime

    def downloadImg(self, imgUrl, fileName):
        """
        下载图片
        :param imgUrl: 图片路径
        :param fileName: 图片名称
        :return:
        """
        img_path = self.config.getValue('img_path')
        # 判断文件夹是否存在
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        # 发请求并保存图片
        suffix = os.path.splitext(imgUrl)[1]
        if suffix == '':
            suffix = '.jpg'
        r = None
        try:
            r = requests.get(url=imgUrl, stream=True, proxies=self.proxies)
        except Exception as e:
            self.log.error(e)
            self.log.info(f"下载图片{imgUrl}请求失败,开始重新发起请求")
            for i in range(5):
                try:
                    self.proxies = self.zm.getOneProxies()
                    self.log.info(f"当前代理为{self.proxies}")
                    r = requests.get(url=imgUrl, stream=True, proxies=self.proxies)
                    self.log.info(f"第{i + 1}次尝试成功")
                    break
                except Exception as e:
                    self.log.error(e)
                    self.log.info(f"第{i + 1}次尝试失败")
        if r.status_code == 200:
            all_name = fileName + suffix
            open(img_path + all_name, 'wb').write(r.content)
            return all_name
        else:
            return None

    def query_by_key(self, key):
        """
        根据key查询数据
        :param key: 参数
        :return:
        """
        self.log.info(f"正在根据关键词【{key}】查看结果")
        query_res = []
        pram = {
            'title': key,
            'page': '0',
            'sortType': '0',
            'sortMode': '1',
            'limit': '20',
            'showHot': '1',
            'isAggr': '1'
        }
        data = request_util.add_sign(pram)
        url = "https://app.dewu.com/api/v1/h5/search/fire/search/list"
        res = self.try_err_send_request('search', data, url)
        if res.status_code == 200:
            self.log.info(f"根据关键词【{key}】查询请求成功！")
            all_data = res.json()
            for entity in all_data['data']['productList']:
                query_res.append(entity)
        return query_res

    def try_err_send_request(self, send_type, data, url):
        """
        发送请求
        :param send_type:发送类型
        :param data:参数
        :param url:请求路径
        :return:
        """
        res = None
        try:
            res = self.send_request(send_type, data, url)
        except Exception as e:
            self.log.error(e)
            self.log.info(f",发送请求失败，正在尝试重新请求...")
            for i in range(5):
                self.log.info(f"正在尝试第{i + 1}次请求...")
                self.proxies = self.zm.getOneProxies()
                self.log.info(f"当前代理为{self.proxies}")
                try:
                    res = self.send_request(send_type, data, url)
                    self.log.info(f"第{i + 1}次请求成功...")
                    break
                except Exception as e:
                    self.log.error(e)
                    self.log.info(f"第{i + 1}次请求失败...")
        return res

    def send_request(self, send_type, data, url):
        """
        单独发送请求
        :param send_type: 请求类型
        :param url: 请求路径
        :param data: 请求参数
        :return:
        """
        if 'search' == send_type:
            res = requests.get(url=url, params=data, headers=request_util.get_header(send_type),
                               verify=False, timeout=10, proxies=self.proxies)
        else:
            res = requests.post(url=url, json=data, headers=request_util.get_header(send_type),
                                verify=False, timeout=10, proxies=self.proxies)
        return res

    def run(self):
        """
        启动爬虫
        :return:
        """
        self.log.info("正在启动得物爬虫程序...")
        # 获取代理
        self.log.info(f"当前代理:{self.proxies}")
        # 查询所有待查询的商品列表
        commodity_sql = 'SELECT * FROM org_all_commodity'
        commodity_list = self.db.query(commodity_sql)
        for commodity in commodity_list:
            self.log.info(f"开始执行【{commodity[2]}】商品")
            spu_id = commodity[1]
            if commodity[3] == 1:
                data = self.query_by_key(commodity[2])[0]
                spu_id = data['spuId']
                self.get_info(str(spu_id))
                # 修改数据库状态
                update_sql = f'UPDATE org_all_commodity SET is_new = 0,spu_id = {spu_id} WHERE id = {commodity[0]}'
                self.db.executeSql(update_sql)
            self.get_record(spu_id)
            self.log.info(f"商品【{commodity[2]}】执行执行完毕！")

        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log.info(f"{now}程序结束")
