import pandas as pd
import matplotlib.pyplot as plt
import os

from app.db.my_sql_db import MySqlDb
from app.configUtil import ConfigUtil


class Analysis:
    def __init__(self, article_number, _type="Day"):
        self.db = MySqlDb()
        self.engine = self.db.getEngine()
        self.article_number = article_number
        # 保存图片文件夹
        self.save_img_path = ConfigUtil().getValue("analysis_img_path") + self.article_number
        if not os.path.exists(self.save_img_path):
            os.makedirs(self.save_img_path)
        # 查询数据
        sql = f"SELECT * FROM org_purchase_record WHERE article_number = '{article_number}'"
        if _type == "Day":
            sql += "and format_time >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-%d'), INTERVAL 30 DAY)"
        elif _type == "Num":
            sql += "LIMIT 1000"
        self.all_data = pd.read_sql_query(sql, self.engine)
        # 删除求购
        self.data = self.all_data.drop(self.all_data[self.all_data.order_sub_type_name == "求购"].index)
        # 获取求购数据
        self.ask_to_buy = self.all_data[self.all_data["order_sub_type_name"] == "求购"]
        # 获取时间
        self.date = self.data.format_time.drop_duplicates().sort_values(ascending=False).values
        # 获取尺码
        self.size = self.data.properties_values.drop_duplicates().sort_values(ascending=False).values

        # 基础属性
        self.max_price = self.data.price.max()
        self.min_price = self.data.price.min()
        self.avg_price = self.data.price.mean()
        self.all_volume = self.data.shape[0]

        # 图片属性
        self.image_wide = 15
        self.image_high = 10

    def get_price_volume(self, chart_type="日期"):
        """
        统计价格-销量
        :return:
        """
        # 根绝时间分组的价格
        price = self.data.groupby('format_time' if chart_type == "日期" else 'properties_values')['price'].mean()
        counts = self.data.groupby('format_time' if chart_type == "日期" else 'properties_values')['price'].count().values

        # 绘图
        fig = plt.figure(figsize=(self.image_wide, self.image_high))
        fig.suptitle(f"{chart_type}-价格-销量趋势图(30天)")
        p = fig.add_subplot(111)
        p.set_ylabel("价格")
        p.set_xlabel(chart_type)
        p.plot(self.date if chart_type == "日期" else self.size, price)
        c = p.twinx()
        c.set_ylabel("交易量")
        ca = c.bar(self.date if chart_type == "日期" else self.size, counts, alpha=0.3)
        fig.legend(['平均价格', '交易量'])
        self.__auto_text(ca)
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

    def get_repeat_num(self):
        """
        生成交易量重复图
        :return:
        """
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
        self.__auto_text(res)
        plt.title("重复交易量试图")
        plt.xlabel("重复频率")
        plt.ylabel("重复交易数量")
        plt.savefig(self.save_img_path + "/重复交易量试图.jpg")

    def update_info(self):
        """
        更新基础属性
        :return:
        """
        # 获取数据
        recommended_size = self.data.groupby("properties_values")["id"].count().reset_index(name="count") \
            .sort_values("count", ascending=False).head(3).properties_values.values
        s = ",".join(recommended_size)
        print(s)
        # 持久化
        # query_info_sql = f"SELECT * FROM org_data_analysis_info WHERE article_number = '{self.article_number}'"
        # info = self.db.getOne(query_info_sql)
        # if info:
        #     # 更新
        #     pass
        # else:
        #     # 插入
        #     pass

    def get_ask_to_buy(self):
        """
        绘制求购数据
        :return:
        """
        # 获取数据
        size = self.ask_to_buy.groupby("properties_values")["id"].count()
        date = self.ask_to_buy.groupby("format_time")["id"].count()

        size_index = size.index.values
        date_index = pd.to_datetime(date.index.values, format="%Y-%m-%d")

        size_data = size.values
        date_data = date.values

        # 绘图
        fig = plt.figure(figsize=(self.image_wide, self.image_high))
        size_plt = fig.add_subplot(211)
        size_plt.set_title("尺码-求购量图")
        size_plt.set_ylabel("求购量")
        size_plt.set_xlabel("尺码")
        size_plt.bar(size_index, size_data)

        date_plt = fig.add_subplot(212)
        date_plt.set_title("日期-求购量图")
        date_plt.set_ylabel("求购量")
        date_plt.set_xlabel("日期")
        date_plt.bar(date_index, date_data)
        plt.show()

    @staticmethod
    def __auto_text(rects):
        for rect in rects:
            plt.text(rect.get_x(), rect.get_height(), rect.get_height(), va='bottom')