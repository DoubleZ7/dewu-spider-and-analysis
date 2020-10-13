import json
import time
import mitmproxy

from mysql_db import mysqlDb

detailUrl = 'https://app.dewu.com/api/v1/app/index/ice/flow/product/detail'
lastSoldUrl = 'https://app.dewu.com/api/v1/app/commodity/ice/last-sold-list'
db = mysqlDb()

entity = None


def response(flow):
    """
    根据路径判断请求数据
    :param flow:
    :return:
    """
    global entity
    requestUrl = flow.request.url
    if detailUrl in requestUrl:
        entity = getDetail(flow)
        if not entity[0]:
            detailSql = 'INSERT INTO t_org_detail VALUES(%s, %s, %s, %s, %s, %s, %s)'
            db.insertData(detailSql, entity)
    if lastSoldUrl in requestUrl and entity:
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
    allData = json.loads(flow.response.text)
    dataList = allData.get('data').get('list')
    recordList = []
    articleNumber = entity[6]
    getNewestSql = "SELECT * FROM t_org_purchase_record WHERE id = (SELECT MAX(id) FROM t_org_purchase_record WHERE " \
                   "article_number = '{}') ".format(articleNumber)
    newest = db.getOne(getNewestSql)
    for d in dataList:
        record = (
            None,
            articleNumber,
            d['userName'],
            d['formatTime'],
            d['price'] / 100,
            d['orderSubTypeName'],
            d['propertiesValues'],
            entity[1]
        )
        recordList.append(record)
    return recordList


if __name__ == '__main__':
    d1 = (
        None,
        'CN1084-200',
        '单*c',
        '2020-10-11 03:11:21',
        4299,
        '',
        '42.5',
        '2020-10-11 03:11:21'
    )
    # sql = 'INSERT INTO t_org_purchase_record VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
    # db.insertData(sql, d1)
    queryByArticleNumberSql = "SELECT * FROM t_org_detail WHERE article_number = '{}'".format('AT3102-201')
    data = db.getOne(queryByArticleNumberSql)
    if data:
        print('现在是null')
    else:
        print('现在不是NULL')
