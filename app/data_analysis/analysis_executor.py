import time

from app.data_analysis.analysis import Analysis
from app.data_analysis.generate_reports import GenerateReports
from app.log import Logger
from app.db.my_sql_db import MySqlDb
from app.decorator.decorator import error_repeat


class AnalysisExecutor:
    def __init__(self):
        self.db = MySqlDb()
        self.log = Logger().logger
        self.thread_count = 4

    def update_all_data(self):
        """
        更新所有商品信息数据
        :return:
        """
        self.log.info("正在启动单线程数据分析程序...")
        # 查询所有已有记录的商品列表
        commodity_sql = 'SELECT * FROM org_all_commodity WHERE is_new = 0'
        commodity_list = self.db.query(commodity_sql)
        article_number_list = [com[2] for com in commodity_list]

        # with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
        #     executor.map(self.update_one_date, article_number_list)

        for commodity in article_number_list:
            # 一个月数据
            self.update_one_month(commodity)
            self.reports_one_month(commodity)

            # 三个月数据
            self.update_three_month(commodity)
            self.reports_three_month(commodity)

        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log.info(f"{now}程序结束")

    @error_repeat
    def update_one_month(self, article_number):
        """
        更新一个月数据
        :param article_number:
        :return:
        """
        self.log.info(f"正在对【{article_number}】进行一个月数据分析")
        an = Analysis(article_number)
        an.run_analysis()
        self.log.info(f"【{article_number}】数据分析完成")

    @error_repeat
    def update_three_month(self, article_number):
        """
        更新三个月数据
        :param article_number:
        :return:
        """
        self.log.info(f"正在对【{article_number}】进行三个月数据分析")
        an = Analysis(article_number, _type='three_month')
        an.run_analysis()
        self.log.info(f"【{article_number}】数据分析完成")

    @error_repeat
    def reports_one_month(self, article_number):
        """
        生成一个月的数据报告
        :param article_number:
        :return:
        """
        self.log.info(f"正在生成【{article_number}】一个月数据分析报告")
        gen = GenerateReports(article_number)
        gen.generate()
        self.log.info(f"【{article_number}】一个月数据分析报告生成成功")

    @error_repeat
    def reports_three_month(self, article_number):
        """
        生成三个月的数据报告
        :param article_number:
        :return:
        """
        self.log.info(f"正在生成【{article_number}】三个月数据分析报告")
        gen = GenerateReports(article_number, reports_type="three_month")
        gen.generate()
        self.log.info(f"【{article_number}】三个月数据分析报告生成成功")