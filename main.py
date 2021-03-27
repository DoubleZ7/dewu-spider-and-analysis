from apscheduler.schedulers.blocking import BlockingScheduler
from app import de_wu_spider
from app.log import Logger

log = Logger().logger


def run():
    # 添加定时器
    log.info("爬虫程序定时器已启动")
    scheduler = BlockingScheduler()
    scheduler.add_job(de_wu_spider.run, 'cron', hour=18, minute=5)
    scheduler.start()


if __name__ == '__main__':
    run()