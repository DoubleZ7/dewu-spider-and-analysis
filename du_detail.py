import json
import time
import datetime
import requests
import os.path
import mitmproxy

from mysql_db import mysqlDb
from configUtil import ConfigUtil

detailUrl = 'https://app.dewu.com/api/v1/app/index/ice/flow/product/detail'
lastSoldUrl = 'https://app.dewu.com/api/v1/app/commodity/ice/last-sold-list'
db = mysqlDb()
config = ConfigUtil()

entity = None
newest = None
flag_is_do = 1


def response(flow):
    """
    根据路径判断请求数据
    :param flow:
    :return:
    """
    global entity
    global newest
    requestUrl = flow.request.url

    print("--------------进入了详情--------------------")
    print("--------------请求地址--------------------")
    print(requestUrl)

    # 判断是否是获取商品详情的URL
    if detailUrl in requestUrl:
        global flag_is_do
        # 每次进入一次详情重置一次是否继续查询标识
        flag_is_do = 1
        # 获取当前商品的信息（每个商品只获取一次）
        entity, imgList = getDetail(flow)
        # 获取当前商品的最新一条交易记录（每个商品只获取一次）
        # getNewestSql = "SELECT * FROM org_purchase_record WHERE id = ((SELECT MAX(id) FROM org_purchase_record " \
                       # "WHERE article_number = '{}')) ".format(entity[6])
        getNewestSql = "select * from org_purchase_record r WHERE article_number='{}' ORDER BY ABS(NOW() - " \
                       "r.format_time) ASC limit 1".format(entity[6])
        newest = db.getOne(getNewestSql)
        if not entity[0]:
            # 插入详情
            detailSql = 'INSERT INTO org_detail VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            db.insertData(detailSql, entity)
            # 插入详情图片
            insertImgSql = 'INSERT INTO org_detail_img VALUES(%s, %s, %s, %s, %s, %s)'
            db.insertDataList(insertImgSql, imgList)
        else:
            # 修改商品更新状态
            updateSql = "UPDATE org_detail SET is_update = 1 where article_number='{}'".format(entity[6])
            db.executeSql(updateSql)

    # 判断是否是获取商品详情的URL，当前商品是否存在，是否需要继续爬取
    if lastSoldUrl in requestUrl and entity and flag_is_do == 1:
        dataList = getLastSoldList(flow)
        insertSql = 'INSERT INTO org_purchase_record VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
        db.insertDataList(insertSql, dataList)


def getDetail(flow):
    """
    获取单件商品的详情
    :param flow:
    :return:返回单件商品的详情实体
    """
    allData = json.loads(flow.response.text)
    data = allData.get('data')
    # 详情
    pageDetail = data.get('detail')
    articleNumber = pageDetail.get('articleNumber')
    detail = db.getOne("SELECT * FROM org_detail WHERE article_number = '{}'".format(articleNumber))
    imgList = []
    if not detail:
        # 参数
        baseProperties = data.get('baseProperties')
        brandList = baseProperties["brandList"]
        parameterList = baseProperties["list"]
        parameters = getParameter(parameterList)

        # 图片
        imageAndText = data.get("imageAndText")
        images = imageAndText[1].get("images")
        imgList = getImgUrl(images, articleNumber)
        # 下载logo
        logoUrl = downloadImg(pageDetail["logoUrl"], articleNumber)
        detail = (
            None,
            pageDetail.get('title'),
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
            None,
            1
        )
    return detail, imgList


def getLastSoldList(flow):
    """
    第一次获取单件商品的销售记录
    :param flow:
    :return:返回20个销售记录
    """
    global flag_is_do
    allData = json.loads(flow.response.text)
    dataList = allData.get('data').get('list')
    recordList = []
    articleNumber = entity[6]
    for d in dataList:
        # 判断是否是当天的数据 如果是则放入集合，如果不是则跳出循环标识不再获取交易记录
        if newest:
            if compareRecord(newest, d):
            # if '天' in formatTime or '月' in formatTime:
                flag_is_do = 0
                break
        formatTime = d['formatTime']
        formatTime = refactorFormatTime(formatTime)
        record = (
            None,
            articleNumber,
            d['userName'],
            formatTime,
            d['price'] / 100,
            d['orderSubTypeName'],
            d['propertiesValues'],
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        recordList.append(record)
    return recordList[::-1]


def compareRecord(dbData, record):
    """
    比较两条记录是否相等
    :param dbData:
    :param record:
    :return:
    """
    for i in range(len(record)):
        if i == 0 or i == 3 or i == 7:
            continue
        if i == 4:
            price = dbData[i]
            if not int(price) == record[i]:
                return False
        if not dbData[i] == record[i]:
            return False
    return True


def refactorFormatTime(formatTime):
    """
    重构交易时间返回数据类型yyyy-MM-dd
    :param formatTime:
    :return:
    """
    y = time.strftime("%Y", time.localtime())
    if '前' in formatTime:
        if '小时' in formatTime:
            h = formatTime[0:formatTime.find('小')]
            newTime = (datetime.datetime.now() + datetime.timedelta(hours=-int(h))).strftime("%Y-%m-%d")
        else:
            newTime = datetime.datetime.now().strftime("%Y-%m-%d")
        if '天' in formatTime:
            dd = formatTime[0:formatTime.find('天')]
            newTime = (datetime.datetime.now() + datetime.timedelta(days=-int(dd))).strftime("%Y-%m-%d")
    else:
        newTime = y + '-' + formatTime.replace('月', '-').replace('日', '')
    return newTime


def getParameter(parameterList):
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


def getImgUrl(images, articleNumber):
    """
    获取图片URL
    :param images:
    :return:
    """
    imgList = []
    count = 1
    for g in images:
        u = downloadImg(g["url"], articleNumber + str(count))
        height = g["height"]
        if height > 100:
            img = (
                None,
                articleNumber,
                u,
                count,
                g["width"],
                g["height"]
            )
            imgList.append(img)
            count += 1
    return imgList


def downloadImg(imgUrl, fileName):
    suffix = os.path.splitext(imgUrl)[1]
    if suffix == '':
        suffix = '.jpg'
    host = config.getValue("web")["host"]
    port = config.getValue("web")["port"]
    imgPath = config.getValue("web")["imgUrl"]
    url = "http://" + host + ":" + port + imgPath
    data = {"url": imgUrl, "fileName": fileName, "suffix": suffix}
    r = requests.post(url, data=data)
    return host + ":" + port + "/static/images/" + fileName + suffix


if __name__ == '__main__':
    detail = db.getOne("SELECT * FROM org_detail WHERE article_number = '{}'".format('CK4344-002'))
    print(detail)
