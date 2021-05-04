# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base  # 模型继承父类
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR, TINYINT, DATE, DATETIME, TEXT  # 导入数据类型
from sqlalchemy import Column  # 指定字段

Base = declarative_base()

"""
id 编号 大整型 主键
name 姓名 字符串 非空
job 职位 小整型 非空
sex 性别 小整型 非空
edu 学历 小整型 非空
birth 生日 日期 非空
email 邮箱 字符串 非空 唯一
phone 手机 字符串 非空 唯一
info 介绍 文本 非空
face 头像 字符串 非空
createdAt 添加时间 日期时间 非空
updatedAt 修改时间 日期时间 非空
"""


# 员工模型
class Employee(Base):
    __tablename__ = "employee"
    id = Column(BIGINT, primary_key=True)
    name = Column(VARCHAR(255), nullable=False)
    job = Column(TINYINT, nullable=False)
    sex = Column(TINYINT, nullable=False)
    edu = Column(TINYINT, nullable=False)
    birth = Column(DATE, nullable=False)
    email = Column(VARCHAR(100), nullable=False, unique=True)
    phone = Column(VARCHAR(11), nullable=False, unique=True)
    info = Column(TEXT, nullable=False)
    face = Column(VARCHAR(100), nullable=False)
    createdAt = Column(DATETIME, nullable=False)
    updatedAt = Column(DATETIME, nullable=False)


"""
id 编号 大整型 主键
emoployee_id 员工编号 大整型 非空
hobby_key 爱好索引 小整型 非空
createdAt 添加时间 日期时间 非空
updatedAt 修改时间 日期时间 非空
"""


# 爱好数据模型
class Hobby(Base):
    __tablename__ = "hobby"
    id = Column(BIGINT, primary_key=True)
    employee_id = Column(BIGINT, nullable=False)
    hobby_key = Column(TINYINT, nullable=False)
    createdAt = Column(DATETIME, nullable=False)
    updatedAt = Column(DATETIME, nullable=False)


if __name__ == "__main__":
    import mysql.connector  # 导入数据库连接驱动
    from sqlalchemy import create_engine  # 导入创建引擎工具

    mysql_configs = dict(
        db_host="127.0.0.1",
        db_name="crud",
        db_port=3306,
        db_user="root",
        db_pwd="root"
    )

    engine = create_engine(
        'mysql+mysqlconnector://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}?charset=utf8'.format(
            **mysql_configs
        ),
        encoding="utf-8",
        echo=True
    )

    metadata = Base.metadata
    metadata.create_all(engine)
    print("生成成功！")
