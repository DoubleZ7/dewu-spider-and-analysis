import yaml
import logging
import datetime
import os


class Logger:
    """自定义封装logging模块"""

    def __init__(self, default_level=logging.INFO):
        # 加载配置文件地址
        cur_path = os.path.dirname(__file__)
        self.config_path = cur_path + "/config.yaml"

        # 初始化一个logger
        self.logger = logging.getLogger('__name__')
        self.default_level = default_level
        logger_main_level, logger_file_level, logger_console_level = self.config()
        self.logger.setLevel(logger_main_level)
        fomatter = logging.Formatter(
            '[%(asctime)s] %(filename)s line:%(lineno)d [%(levelname)s]%(message)s')
        # 初始化输出到日志文件的handle
        file_name = self.getLogFilePath() + '/{}log.txt'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
        file_log = logging.FileHandler(filename=file_name, encoding='utf-8')
        file_log.setLevel(logger_file_level)
        file_log.setFormatter(fomatter)
        # 初始化增加输出到控制台的handle
        console_log = logging.StreamHandler()
        console_log.setLevel(logger_console_level)
        console_log.setFormatter(fomatter)

        if self.logger.hasHandlers() is False:
            self.logger.addHandler(file_log)
            self.logger.addHandler(console_log)
        # self.logger.removeHandler(file_log)
        # self.logger.removeHandler(console_log)
        file_log.close()
        console_log.close()

    def config(self):
        """
        :return: 返回配置中读取的level
        """
        try:

            with open(self.config_path, 'r', encoding='utf-8') as f:
                global config_data
                config_data = yaml.load(f, Loader=yaml.FullLoader)
        except IOError as e:
            print(e)
            self.logger.error('open config file failed')
        case1 = config_data['logConfig']['testLogLevel']['mainLogLevel']
        case2 = config_data['logConfig']['testLogLevel']['fileLogLevel']
        case3 = config_data['logConfig']['testLogLevel']['consoleLogLevel']
        logger_main_level = self.switch(case=case1)
        logger_file_level = self.switch(case=case2)
        logger_console_level = self.switch(case=case3)
        log_file_path = config_data['logConfig']['logFilePath']
        return logger_main_level, logger_file_level, logger_console_level

    def getLogFilePath(self):
        """
        获取配置文件中的看日志存放路径
        :return:
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                global config_data
                config_data = yaml.load(f, Loader=yaml.FullLoader)
        except IOError:
            self.logger.error('open config file failed')
        return config_data['logConfig']['logFilePath']

    def switch(self, case):
        """
        :param case: 传入需要做判断的level
        :return: 返回最终的level
        """
        if case == 'DEBUG':
            result = logging.DEBUG
        elif case == 'INFO':
            result = logging.DEBUG
        elif case == 'ERROR':
            result = logging.ERROR
        elif case == 'CRITICAL':
            result = logging.CRITICAL
        else:
            result = self.logger.setLevel(self.default_level)
        return result

    def log(self):
        return self.logger


if __name__ == '__main__':
    # log = Logger()
    # print(log.getLogFilePath())

    with open('config.yaml', 'r') as f:
        print(f.readline())
