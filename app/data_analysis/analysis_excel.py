import pandas as pd
import matplotlib.pyplot as plt
import os

from app.db.my_sql_db import MySqlDb
from app.configUtil import ConfigUtil


class AnalysisExcel:
    def __init__(self, article_number, _type="Day"):
        self.engine = MySqlDb().getEngine()
        self.article_number = article_number
        # 保存图片文件夹
        self.save_img_path = ConfigUtil().getValue("analysis_img_path") + self.article_number
        if not os.path.exists(self.save_img_path):
            os.makedirs(self.save_img_path)
        sql = f"SELECT * FROM org_purchase_record WHERE article_number = '{article_number}'"
        if _type == "Day":
            sql += "and format_time >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-%d'), INTERVAL 7 DAY)"
        elif _type == "Num":
            sql += "LIMIT 1000"
        self.data = pd.read_sql_query(sql, self.engine)

    def get_date_price_avg(self):
        """
        统计时间-价格
        :return:
        """
        # 根绝时间分组的价格
        groups = self.data.groupby('时间')['价格'].mean()
        groups.plot()

    def get_date_sales_volume(self):
        """
        统计时间-销量
        :return:
        """
        groups = self.data.groupby('时间')['价格'].count()
        groups.plot(kind="bar")

    def get_size_sales_volume(self):
        """
        统计尺码-销量
        :return:
        """
        groups = self.data.groupby('码数规格')['价格'].count()
        groups.plot(kind="bar")
        plt.show()

    def get_user_repeat(self):
        """
        统计用户重复率
        :return:
        """
        # 根据用户名分组的重复率
        users = self.data.groupby('user_name')['price'].count().reset_index(name='数量').sort_values('数量', ascending=False).head(20)
        users.set_index('user_name').plot(kind="bar")
        plt.title("用户重复购买数量")
        plt.xlabel("用户名称")
        plt.ylabel("数量")
        plt.xticks(rotation=45, fontsize=9, verticalalignment='top', fontweight='light')
        plt.show()

    @staticmethod
    def auto_text(rects):
        for rect in rects:
            plt.text(rect.get_x(), rect.get_height(), rect.get_height(), va='bottom')

    def get_repeat_num(self):
        # 计算交易数量
        counts = self.data.user_name.value_counts()
        two_count = 0
        three_count = 0
        four_count = 0
        for count in counts:
            if count > 1:
                two_count += count
            if count > 2:
                three_count += count
            if count > 3:
                four_count += count
        # 绘图
        index_list = ["大于两次", "大于三次", "大于四次"]
        data = [two_count, three_count, four_count]
        res = plt.bar(index_list, data)
        self.auto_text(res)
        plt.title("重复交易量试图")
        plt.xlabel("重复频率")
        plt.ylabel("重复交易数量")
        plt.savefig(self.save_img_path + "/重复交易量试图.jpg")