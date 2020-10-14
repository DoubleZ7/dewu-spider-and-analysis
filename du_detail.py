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
    if detailUrl in requestUrl:
        # 获取当前商品的信息（每个商品只获取一次）
        entity = getDetail(flow)
        # 获取当前商品的最新一条交易记录（每个商品只获取一次）
        getNewestSql = "SELECT * FROM t_org_purchase_record WHERE id = (SELECT MAX(id) FROM t_org_purchase_record " \
                       "WHERE article_number = '{}') ".format(entity[6])
        newest = db.getOne(getNewestSql)
        if not entity[0]:
            detailSql = 'INSERT INTO t_org_detail VALUES(%s, %s, %s, %s, %s, %s, %s)'
            db.insertData(detailSql, entity)
    if lastSoldUrl in requestUrl and entity and flag_is_do == 1:
        dataList = getLastSoldList(flow)
        insertSql = 'INSERT INTO t_org_purchase_record VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
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
    detail = db.getOne("SELECT * FROM t_org_detail WHERE article_number = '{}'".format(articleNumber))
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
    获取单件商品的销售记录
    :param flow:
    :return:返回20个销售记录
    """
    global newest
    global flag_is_do
    allData = json.loads(flow.response.text)
    dataList = allData.get('data').get('list')
    recordList = []
    articleNumber = entity[6]
    for d in dataList:
        formatTime = refactorFormatTime(d['formatTime'])
        record = (
            None,
            articleNumber,
            d['userName'],
            formatTime,
            d['price'] / 100,
            d['orderSubTypeName'],
            d['propertiesValues'],
            entity[1]
        )
        if not newest and compareRecord(newest, record):
            flag_is_do = 0
            break
        else:
            recordList.append(record)
    return recordList


def compareRecord(dbData, record):
    """
    比较两条记录是否相等
    :param dbData:
    :param record:
    :return:
    """
    for i in range(len(record)):
        if i == 0:
            continue
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
    formatTime = '10月6日'
    d = refactorFormatTime(formatTime)
    print(d)

