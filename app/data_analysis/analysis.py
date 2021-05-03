import pandas as pd
import matplotlib.pyplot as plt
import os
import time

from app.db.my_sql_db import MySqlDb
from app.configUtil import ConfigUtil
from decimal import Decimal
from app.log import Logger


class Analysis:
    def __init__(self, article_number, _type="Day"):
        self.db = MySqlDb()
        self.engine = self.db.getEngine()
        self.log = Logger().logger
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

        # 图片属性
        self.image_wide = 15
        self.image_high = 10

        # plt.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei', 'FangSong']  # 汉字字体,优先使用楷体，如果找不到楷体，则使用黑体
        # plt.rcParams['font.size'] = 12  # 字体大小
        # plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

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

        # 修改保存路径
        img_path = "/date_price_volume.jpg" if chart_type == "日期" else "/size_price_volume.jpg"
        plt.savefig(self.save_img_path + img_path)

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
        plt.savefig(self.save_img_path + "/user_repeat.jpg")

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
        plt.savefig(self.save_img_path + "/repeat_num.jpg")

    def update_info(self):
        """
        更新基础属性
        :return:
        """
        # 获取数据
        recommended_size = self.data.groupby("properties_values")["id"].count().reset_index(name="count") \
            .sort_values("count", ascending=False).head(3).properties_values.values
        r_size = ",".join(recommended_size)

        # 基础属性
        max_price = self.data.price.max()
        min_price = self.data.price.min()
        avg_price = round(self.data.price.mean(), 2)
        all_volume = self.data.shape[0]

        # 计算溢价
        auth_price = self.db.getOne(f"SELECT auth_price FROM org_detail WHERE article_number = '{self.article_number}'")[0]
        premium = round((Decimal(avg_price) - auth_price) / auth_price * 100, 2)

        # 持久化
        query_info_sql = f"SELECT * FROM org_data_analysis_info WHERE article_number = '{self.article_number}'"
        info = self.db.getOne(query_info_sql)
        if info:
            # 更新
            update_sql = f"UPDATE org_data_analysis_info " \
                         f"SET max_price = {max_price}, avg_price = {avg_price}, min_price = {min_price}, " \
                         f"premium = {premium},all_volume = {all_volume},recommended_size = '{r_size}'," \
                         f"update_time = '{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}' " \
                         f"WHERE article_number = '{self.article_number}'"
            self.db.executeSql(update_sql)
        else:
            # 插入
            info = (
                None,
                self.article_number,
                0,
                max_price,
                avg_price,
                min_price,
                premium,
                all_volume,
                r_size,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            )
            insert_sql = "INSERT INTO org_data_analysis_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            self.db.insertData(sql=insert_sql, data=info)

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
        plt.savefig(self.save_img_path + "/ask_to_buy.jpg")

    def run_analysis(self):
        """
        数据分析
        :return:
        """
        # 修改信息
        self.log.info(f"正在更新【{self.article_number}】交易信息")
        self.update_info()
        self.log.info(f"【{self.article_number}】交易信息更新完成！")

        # 生成日期价格图
        self.log.info(f"正在生成【{self.article_number}】日期价格图")
        self.get_price_volume()
        self.log.info(f"【{self.article_number}】日期价格图生成完毕！")

        # 生成尺码价格图
        self.log.info(f"正在生成【{self.article_number}】尺码价格图")
        self.get_price_volume(chart_type="尺码")
        self.log.info(f"【{self.article_number}】尺码价格图生成完毕！")

        # 生成求购图
        self.log.info(f"正在生成【{self.article_number}】求购图")
        self.get_ask_to_buy()
        self.log.info(f"【{self.article_number}】求购图生成完毕")
        # 生成推荐尺码移动平均线图
        # 生成推荐尺码K线图

    @staticmethod
    def __auto_text(rects):
        for rect in rects:
            plt.text(rect.get_x(), rect.get_height(), rect.get_height(), va='bottom')