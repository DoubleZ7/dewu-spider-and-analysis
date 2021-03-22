import yaml
import random
from log import Logger

log = Logger().log()


class ConfigUtil:
    def __init__(self):
        self.configPath = "./config.yaml"

    def readYaml(self):
        # read config from yaml document
        file = self.configPath
        try:
            f = open(file, 'r', encoding='UTF-8')
            global configData
            configData = yaml.load(f, Loader=yaml.FullLoader)
        except IOError:
            log.info('open config failed')
        return configData

    def getValue(self, key):
        return self.readYaml()[key]

    def randomGetUserAgent(self):
        return random.choice(self.readYaml()['User_Agents'])


if __name__ == '__main__':
    config = ConfigUtil()
    data = config.getValue('db')['host']
    print(data)
