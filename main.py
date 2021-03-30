from apscheduler.schedulers.blocking import BlockingScheduler
from app.de_wu_spider import DeWuSpider
from app.log import Logger

log = Logger().logger


def run():
    # 添加定时器
    log.info("爬虫程序定时器已启动")
    scheduler = BlockingScheduler()
    spider = DeWuSpider()
    scheduler.add_job(spider.run, 'cron', hour=00)
    # scheduler.add_job(spider.run, 'cron', hour=12)
    scheduler.start()


if __name__ == '__main__':
    run()