import pandas as pd

# 引入資料庫包
import pymysql

# 建立資料庫的連線
conn = pymysql.connect(host='localhost', user='root',
                       passwd='f2f54321', db='test2', charset='utf8')

# 獲取遊標
cursor = conn.cursor()

sql = (
        "SELECT * FROM `temp`"
    )

try:
    # 執行sql語句
    cursor.execute(sql)

    result = cursor.fetchall()

    # 提交到資料庫執行
    conn.commit()
except:
    # 如果發生錯誤則回滾
    conn.rollback()

# 關閉遊標
cursor.close()

# 關閉資料庫
conn.close()

print(result)