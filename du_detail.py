import json
import time
import datetime
import mitmproxy

from mysql_db import mysqlDb

detailUrl = 'https://app.dewu.com/api/v1/app/index/ice/flow/product/detail'
lastSoldUrl = 'https://app.dewu.com/api/v1/app/commodity/ice/last-sold-list'
db = mysqlDb()

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
    # 判断是否是获取商品详情的URL
    if detailUrl in requestUrl:
        global flag_is_do
        # 每次进入一次详情重置一次是否继续查询标识
        flag_is_do = 1
        # 获取当前商品的信息（每个商品只获取一次）
        entity = getDetail(flow)
        # 获取当前商品的最新一条交易记录（每个商品只获取一次）
        getNewestSql = "SELECT * FROM org_purchase_record WHERE id = ((SELECT MAX(id) FROM org_purchase_record " \
                       "WHERE article_number = '{}')) ".format(entity[6])
        newest = db.getOne(getNewestSql)
        if not entity[0]:
            detailSql = 'INSERT INTO org_detail VALUES(%s, %s, %s, %s, %s, %s, %s)'
            db.insertData(detailSql, entity)
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
    d = allData.get('data').get('detail')
    articleNumber = d.get('articleNumber')
    detail = db.getOne("SELECT * FROM org_detail WHERE article_number = '{}'".format(articleNumber))
    if not detail:
        detail = (
            None,
            d.get('title'),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            d.get('authPrice'),
            d.get('sellDate'),
            articleNumber
        )
    return detail


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
        formatTime = d['formatTime']
        # 判断是否是当天的数据 如果是则放入集合，如果不是则跳出循环标识不再获取交易记录
        if newest:
            if '天' in formatTime or '月' in formatTime:
                flag_is_do = 0
                break
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
        newTime = datetime.datetime.now().strftime("%Y-%m-%d")
        if '天' in formatTime:
            dd = formatTime[0:formatTime.find('天')]
            newTime = (datetime.datetime.now() + datetime.timedelta(days=-int(dd))).strftime("%Y-%m-%d")
    else:
        newTime = y + '-' + formatTime.replace('月', '-').replace('日', '')
    return newTime


if __name__ == '__main__':
    getNewestSql = "SELECT * FROM org_purchase_record WHERE id = ((SELECT MAX(id) FROM org_purchase_record " \
                   "WHERE article_number = '{}') + 20) ".format('CV3583-003')
    newest = db.getOne(getNewestSql)
    print(newest)