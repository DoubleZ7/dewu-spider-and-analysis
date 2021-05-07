import docxtpl
import os

from docx.shared import Mm
from app.db.my_sql_db import MySqlDb
from app.configUtil import ConfigUtil
from app.log import Logger
from app.data_analysis.analysis import Analysis


class GenerateReports:
    """
    生成数据分析报告
    """

    def __init__(self, article_number, reports_type="one_month"):
        self.article_number = article_number
        self.temp_path = os.path.dirname(os.path.dirname(__file__)) + "/static/data_analysis_tpl.docx"
        self.reports_type = reports_type
        self.db = MySqlDb()
        self.log = Logger().logger
        conf = ConfigUtil()
        self.img_path = conf.getValue("img_path") + self.article_number + ".jpg"
        self.analysis_img_path = conf.getValue("analysis_img_path") + self.article_number

    def generate(self):
        # 基础数据
        detail_sql = f"SELECT title,auth_price,sell_date,brand FROM org_detail " \
                     f"WHERE article_number ='{self.article_number}'"
        detail = self.db.getOne(detail_sql)
        daily_docx = docxtpl.DocxTemplate(self.temp_path)
        print(self.img_path)
        logo_img = docxtpl.InlineImage(daily_docx, self.img_path, width=Mm(140))

        # 基础分析数据
        an = Analysis(self.article_number, self.reports_type)
        info = an.analysis_info()

        # 分析图
        size_price_volume = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                                + f'/size_price_volume_{self.reports_type}.jpg', width=Mm(140))
        date_price_volume = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                                + f'/date_price_volume_{self.reports_type}.jpg', width=Mm(140))
        ask_to_buy = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                         + f'/ask_to_buy_{self.reports_type}.jpg', width=Mm(140))
        ma = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                 + f'/ma_{self.reports_type}.jpg', width=Mm(140))
        user_repeat = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                          + f'/user_repeat_{self.reports_type}.jpg', width=Mm(140))
        repeat_num = docxtpl.InlineImage(daily_docx, self.analysis_img_path
                                         + f'/repeat_num_{self.reports_type}.jpg', width=Mm(140))

        # 渲染内容
        context = {
            "name": detail[0],
            "brand": detail[3],
            "auth_price": detail[1],
            "sell_date": detail[2],
            "recommended_size": info['r_size'],
            "max_price": info['max_price'],
            "min_price": info['min_price'],
            "all_volume": info['all_volume'],
            "premium": info['premium'],
            "avg_price": info['avg_price'],
            "size_price_volume": size_price_volume,
            "date_price_volume": date_price_volume,
            "ask_to_buy": ask_to_buy,
            "ma": ma,
            "user_repeat": user_repeat,
            "repeat_num": repeat_num
        }
        # 渲染docx
        daily_docx.render(context)
        # 保存docx
        daily_docx.save(self.analysis_img_path + '/' + self.article_number + '_' + self.reports_type + ".docx")
