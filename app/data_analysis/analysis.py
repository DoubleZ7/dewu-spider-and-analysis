import pandas as pd
import matplotlib.pyplot as plt
import os
import time

from app.configUtil import ConfigUtil
from decimal import Decimal
from app.log import Logger


class Analysis:
    def __init__(self, article_number, db, _type="one_month"):
        self.db = db
        self.engine = self.db.getEngine()
        self.log = Logger().logger
        self.article_number = article_number
        self.type = _type
        # 保存图片文件夹
        self.save_img_path = ConfigUtil().getValue("analysis_img_path") + self.article_number
        if not os.path.exists(self.save_img_path):
            os.makedirs(self.save_img_path)
        # 查询数据
        sql = f"SELECT * FROM org_purchase_record WHERE article_number = '{article_number}'"
        if _type == "one_month":
            sql += "and format_time >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-%d'), INTERVAL 30 DAY)"
        elif _type == "three_month":
            sql += "and format_time >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-%d'), INTERVAL 91 DAY)"
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
        self.title_fontsize = 16
        self.label_fontsize = 14

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
        p = fig.add_subplot(111)
        p.set_title(f"{chart_type}-价格-销量趋势图", fontsize=self.label_fontsize)
        p.set_ylabel("价格", fontsize=self.label_fontsize)
        p.set_xlabel(chart_type, fontsize=self.label_fontsize)
        p.plot(self.date if chart_type == "日期" else self.size, price)
        c = p.twinx()
        c.set_ylabel("交易量", fontsize=self.label_fontsize)
        ca = c.bar(self.date if chart_type == "日期" else self.size, counts, alpha=0.3)
        fig.legend(['平均价格', '交易量'])
        # self.__auto_text(ca)

        # 修改保存路径
        img_path = f"/date_price_volume_{self.type}.jpg" if chart_type == "日期" \
            else f"/size_price_volume_{self.type}.jpg"
        fig.savefig(self.save_img_path + img_path)
        plt.close(fig)

    def get_user_repeat(self):
        """
        统计用户重复率
        :return:
        """
        # 根据用户名分组的重复率
        users = self.data.groupby('user_name')['price'].count().reset_index(name='count')\
            .sort_values('count', ascending=False).head(10)
        user_list = users.user_name.tolist()
        count_list = users['count'].tolist()

        # 绘图
        fig = plt.figure(figsize=(self.image_wide, self.image_high))
        user_repeat_plt = fig.add_subplot(111)
        user_repeat_plt.set_title("用户重复购买数量", fontsize=self.title_fontsize)
        user_repeat_plt.set_xlabel("用户名称", fontsize=self.label_fontsize)
        user_repeat_plt.set_ylabel("数量", fontsize=self.label_fontsize)
        user_repeat_plt.bar(user_list, count_list)
        fig.savefig(self.save_img_path + f"/user_repeat_{self.type}.jpg")
        plt.close(fig)

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
        fig = plt.figure(figsize=(self.image_wide, self.image_high))
        repeat_plt = fig.add_subplot(111)
        repeat_plt.set_title("重复交易量试图", fontsize=self.title_fontsize)
        repeat_plt.set_xlabel("重复频率", fontsize=self.label_fontsize)
        repeat_plt.set_ylabel("重复交易数量", fontsize=self.label_fontsize)
        res = repeat_plt.bar(index_list, data)
        # self.__auto_text(res)
        fig.savefig(self.save_img_path + f"/repeat_num_{self.type}.jpg")
        plt.close(fig)

    def analysis_info(self):
        """
        获取基础分析数据
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
        return {
            "r_size": r_size,
            "max_price": max_price,
            "min_price": min_price,
            "avg_price": avg_price,
            "all_volume": all_volume,
            "premium": premium
        }

    def update_info(self):
        """
        更新基础属性
        :return:
        """
        an_info = self.analysis_info()
        # 持久化
        query_info_sql = f"SELECT * FROM org_data_analysis_info WHERE article_number = '{self.article_number}'"
        info = self.db.getOne(query_info_sql)
        if info:
            # 更新
            update_sql = f"UPDATE org_data_analysis_info " \
                         f"SET max_price = {an_info['max_price']}, avg_price = {an_info['avg_price']}," \
                         f"min_price = {an_info['min_price']}, premium = {an_info['premium']}," \
                         f"all_volume = {an_info['all_volume']},recommended_size = '{an_info['r_size']}'," \
                         f"update_time = '{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}' " \
                         f"WHERE article_number = '{self.article_number}'"
            self.db.executeSql(update_sql)
        else:
            # 插入
            info = (
                None,
                self.article_number,
                0,
                an_info['max_price'],
                an_info['avg_price'],
                an_info['min_price'],
                an_info['premium'],
                an_info['all_volume'],
                an_info['r_size'],
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
        size_plt.set_title("尺码-求购量图", fontsize=self.title_fontsize)
        size_plt.set_ylabel("求购量", fontsize=self.label_fontsize)
        size_plt.set_xlabel("尺码", fontsize=self.label_fontsize)
        size_plt.bar(size_index, size_data)

        date_plt = fig.add_subplot(212)
        date_plt.set_title("日期-求购量图", fontsize=self.title_fontsize)
        date_plt.set_ylabel("求购量", fontsize=self.label_fontsize)
        date_plt.set_xlabel("日期", fontsize=self.label_fontsize)
        date_plt.bar(date_index, date_data)
        fig.savefig(self.save_img_path + f"/ask_to_buy_{self.type}.jpg")
        plt.close(fig)

    def run_analysis(self):
        """
        数据分析
        :return:
        """
        if self.type == "one_month":
            # 修改信息
            self.log.info(f"正在更新【{self.article_number}】交易信息")
            self.update_info()
            self.log.info(f"【{self.article_number}】交易信息更新完成")

        # 生成日期价格图
        self.log.info(f"正在生成【{self.article_number}】日期价格图")
        self.get_price_volume()
        self.log.info(f"【{self.article_number}】日期价格图生成完毕")

        # 生成尺码价格图
        self.log.info(f"正在生成【{self.article_number}】尺码价格图")
        self.get_price_volume(chart_type="尺码")
        self.log.info(f"【{self.article_number}】尺码价格图生成完毕")

        # 生成求购图
        self.log.info(f"正在生成【{self.article_number}】求购图")
        self.get_ask_to_buy()
        self.log.info(f"【{self.article_number}】求购图生成完毕")

        # 生成推荐尺码移动平均线图
        self.log.info(f"正在生成【{self.article_number}】SMV图")
        self.get_ma()
        self.log.info(f"【{self.article_number}】SMV图生成完毕")

        # 生成交易量重复图
        self.log.info(f"正在生成【{self.article_number}】交易量重复图")
        self.get_repeat_num()
        self.log.info(f"【{self.article_number}】交易量重复图生成完毕")

        # 生成用户交易量重复图
        self.log.info(f"正在生成【{self.article_number}】用户交易量重复图")
        self.get_user_repeat()
        self.log.info(f"【{self.article_number}】用户交易量重复图生成完毕")

    def __get_recommended_data(self):
        """
        获取推荐尺码所有的数据
        :return:
        """
        recommended_size = self.data.groupby("properties_values")["id"].count().reset_index(name="count") \
            .sort_values("count", ascending=False).head(3).properties_values.values.tolist()
        # 删除非推荐尺码数据
        recommended_data = self.data.drop(self.data[(self.data.properties_values != recommended_size[0])
                                                    & (self.data.properties_values != recommended_size[1])
                                                    & (self.data.properties_values != recommended_size[2])].index)
        return recommended_data

    def get_ma(self):
        """
        绘制移动平均线
        :return:
        """
        # 获取推荐尺码数据
        recommended_data = self.__get_recommended_data()
        data = recommended_data.groupby("format_time")

        # 处理数据
        date_list = []
        avg_list = []
        price_list = []
        for index, d in data:
            one_day = self.__analysis_one_day(d)
            date_list.append(pd.to_datetime(index.value, format="%Y-%m-%d"))
            avg_list.append(one_day['avg_price'])
            price_list.append(one_day['close_price'])

        # 绘图
        fig = plt.figure(figsize=(self.image_wide, self.image_high))
        plot = fig.add_subplot(111)
        plot.set_title("推荐尺码SMA(Simple Moving Average)", fontsize=self.title_fontsize)
        plot.set_xlabel("日期", fontsize=self.label_fontsize)
        plot.set_ylabel("价格", fontsize=self.label_fontsize)
        plot.plot(date_list, avg_list, label="平均线", color="#F08080")
        plot.plot(date_list, price_list, label="价格线", color="#DB7093", linestyle="--")
        plot.legend()
        plot.grid(alpha=0.4, linestyle=':')
        fig.savefig(self.save_img_path + f"/ma_{self.type}.jpg")
        plt.close(fig)

    def get_k_line(self):
        """
        绘制k线图
        :return:
        """
        pass

    @staticmethod
    def __auto_text(rects):
        for rect in rects:
            plt.text(rect.get_x(), rect.get_height(), rect.get_height(), va='bottom')

    @staticmethod
    def __analysis_one_day(data):
        """
        分析一天的数据
        :param data:
        :return:
        """
        max_price = data.price.max()
        min_price = data.price.min()
        avg_price = round(data.price.mean(), 2)
        open_price = data.price.iloc[0]
        close_price = data.price.iloc[data.shape[0] - 1]
        return {
            "max_price": max_price,
            "min_price": min_price,
            "avg_price": avg_price,
            "open_price": open_price,
            "close_price": close_price
        }