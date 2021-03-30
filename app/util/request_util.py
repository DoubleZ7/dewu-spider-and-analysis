import hashlib


def get_sign(params: dict):
    """
    生成签名
    :param params:
    :return:
    """
    sign_string = ''
    sort_params = {k: params[k] for k in sorted(params.keys())}
    for k, v in sort_params.items():
        sign_string += k + v
    # sign_string += "048a9c4943398714b356a696503d2d36"
    sign_string += "19bc545a393a25177083d4a748807cc0"
    m = hashlib.md5()
    m.update(sign_string.encode("utf8"))
    return m.hexdigest()


def get_header(request_type):
    """
    获取请求头
    :return:
    """
    referer = ''
    content_type = 'application/json;charset=UTF-8'
    if request_type == 'info':
        referer = 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/196/page-frame.html'
    elif request_type == 'record':
        referer = 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/202/page-frame.html'
    elif request_type == 'search':
        referer = 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/203/page-frame.html'
        content_type = 'application/x-www-form-urlencoded'
    return {
        'Host': 'app.dewu.com',
        'AppId': 'wxapp',
        'Accept': '*/*',
        'appVersion': '4.4.0',
        'Accept-Language': 'zh-cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'platform': 'h5',
        'Content-Type': content_type,
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.2(0x18000232) NetType/WIFI Language/zh_CN',
        'Referer': referer,
        'Connection': 'keep-alive',
        'Wxapp-Login-Token': ''
    }


def add_sign(params: dict):
    """
    为请求参数添加签名
    :param params:
    :return:
    """
    params['sign'] = get_sign(params)
    return params
