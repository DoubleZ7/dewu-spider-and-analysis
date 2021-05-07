from apscheduler.schedulers.blocking import BlockingScheduler
from app.data_analysis.analysis_executor import AnalysisExecutor
from app.de_wu_spider import DeWuSpider
from app.log import Logger

log = Logger().logger


def run():
    # 添加定时器
    log.info("得物数据分析程序定时器已启动")
    scheduler = BlockingScheduler()
    # 定时爬虫程序
    spider = DeWuSpider()
    scheduler.add_job(spider.thread_run, 'cron', hour=00)
    scheduler.add_job(spider.thread_run, 'cron', hour=12)

    # 数据分析程序
    analysis = AnalysisExecutor()
    scheduler.add_job(analysis.update_all_data, 'cron', day_of_week=0, hour=3)
    scheduler.add_job(analysis.update_all_data, 'cron', hour=0, minute=42)
    scheduler.start()


if __name__ == '__main__':
    run()
