import xlrd

# 獲取一個 Book 物件
book = xlrd.open_workbook("mqtt_pub_test.xlsx")

# 獲取一個 sheet 物件的列表
sheets = book.sheets()

# 每個 Sheet 的名稱
for sheet in sheets:
    print(sheet.name)
    # Sheet 表格內位置
    print(sheet.cell_value(0,0))


topic_list = []
payload_column_num_list = []

# excel row 的數量
topic_list_len = sheets[0].nrows
print(topic_list_len)

# 將 topic 寫入 topic_list
for i in range(1, topic_list_len):
    topic = sheets[0].cell_value(rowx=i, colx=3)
    if topic:
        topic_list.append(topic)
        # 計算 payload column
        payload_column = sheets[0].cell_value(rowx=i, colx=6)
        if payload_column:
            column_num = int(payload_column)
            payload_column_num_list.append(column_num)

print(topic_list)
print(len(topic_list))

print(payload_column_num_list)
print(len(payload_column_num_list))

