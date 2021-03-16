import requests
import json
import time
from utils import request_util

from mysql_db import mysqlDb
from configUtil import ConfigUtil

db = mysqlDb()
config = ConfigUtil()


def get_info(spuId):
    """
    根据spuId获取商品信息
    :param spuId:
    :return:
    """
    data = {
        "spuId": spuId,
        "productSourceName": "",
        "propertyValueId": "0"
    }
    request_util.add_sign(data)
    url = 'https://app.dewu.com/api/v1/h5/index/fire/flow/product/detail'
    requests.packages.urllib3.disable_warnings()
    res = requests.post(url, json=data, headers=request_util.get_header(), verify=False)
    if res.status_code == 200:
        get_detail(res.json())


def get_detail(all_data):
    """
    获取单件商品的详情
    :param all_data:
    :return:返回单件商品的详情实体
    """
    data = all_data.get('data')
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
        parameters = get_parameter(parameterList)

        # 图片
        imageAndText = data.get("imageAndText")
        images = imageAndText[1].get("images")
        imgList = get_img_url(images, articleNumber)
        # 下载logo
        # logoUrl = downloadImg(pageDetail["logoUrl"], articleNumber)
        detail = (
            None,
            pageDetail.get('title'),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            pageDetail.get('authPrice'),
            pageDetail.get('sellDate'),
            articleNumber,
            'logoUrl',
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


def get_img_url(images, article_number):
    """
    获取图片URL
    :param article_number:
    :param images:
    :return:
    """
    imgList = []
    count = 1
    for g in images:
        # u = downloadImg(g["url"], articleNumber + str(count))
        height = g["height"]
        if height > 100:
            img = (
                None,
                article_number,
                'images_url',
                count,
                g["width"],
                g["height"]
            )
            imgList.append(img)
            count += 1
    return imgList


if __name__ == '__main__':
    get_info('1030812')