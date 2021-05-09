from app.log import Logger

log = Logger().log()


def error_repeat(func):
    """
    添加注解的方法在报错之后还会重新执行
    :param func:
    :return:
    """

    def warp(*args, **kwargs):
        try:
            temp = func(*args, **kwargs)
            return temp
        except Exception as e:
            log.info(f"方法{func.__name__}执行报错，报错信息：" + str(e))
            while True:
                try:
                    log.info(f"方法{func.__name__}正在尝试重新执行")
                    temp = func(*args, **kwargs)
                    log.info(f"方法{func.__name__}尝试重新执行成功！")
                    break
                except Exception as e:
                    log.info(f"方法{func.__name__}执行报错，报错信息：" + str(e))
            return temp

    return warp
