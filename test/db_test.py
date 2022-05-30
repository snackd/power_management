import pymysql
import datetime
import time
import csv

db_host = '140.116.39.172'
db_user = 'root'
db_passwd = 'f2f54321'
db_name = 'lvami2'
db_charset = 'utf8'

conn = pymysql.connect(
    host=db_host,
    user=db_user,
    passwd=db_passwd,
    db=db_name,
    charset=db_charset
)

# 獲取遊標
cursor = conn.cursor()
start_time = time.time()
sql = (
    "SELECT * FROM `demand` WHERE `datetime` >= '2017-06-08 00:00:00' AND `datetime` < '2017-06-09 00:00:00'"
)

try:
    # 執行sql語句
    cursor.execute(sql)

    result = cursor.fetchall()
    conn.commit()
except:
    # 如果發生錯誤則回滾
    conn.rollback()

# 關閉遊標
cursor.close()

# 關閉資料庫
conn.close()

# 開啟輸出的 CSV 檔案
with open('yourOutput.csv', 'w', newline='') as csvFile:
    # 建立 CSV 檔寫入器
    writer = csv.writer(csvFile)

    # 指定分隔符號
    writer = csv.writer(csvFile, delimiter=';')

    for i in range(3056):
        # 寫出資料
        writer.writerow(list(temp[i]))
