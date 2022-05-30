# 解析、計算 PM210 回傳的電力參數
def pm210_calculate_value(data_list):

    response = []
    # start_address = 3
    start_address = 11

    # print("LEN:", len(data_list))
    length = len(data_list) - 2
    step = 4

    # print(data_list[start_address-1])
    # print(data_list[start_address])

    for i in range(start_address, length, step):
        LH = data_list[i]  * pow(256, 1)
        LL = data_list[i + 1] * pow(256, 0)
        HH = data_list[i + 2] * pow(256, 3)
        HL = data_list[i + 3] * pow(256, 2)

        power_data = int(LH + LL + HH + HL)

        response.append(power_data)

    return response

def pm210_calculate_value2(data_list):
    # 刪除前三個
    del data_list[:3]

    # 刪除後兩個
    del data_list[-2:]

    # 計算 data_list 長度
    length = len(data_list) / 4
    length = int(length)
    response = []

    for i in range(length):

        # because [] 從 0 開始 ，對應是 (2) + (1)*256 + (4) * 256 ^ 2 + (3) * 256 ^ 3
        LL = data_list[i * 4 + 1] * pow(256, 0)
        LH = data_list[i * 4] * pow(256, 1)
        HL = data_list[i * 4 + 3] * pow(256, 2)
        HH = data_list[i * 4 + 2] * pow(256, 3)

        # LH * 256 + LL + HH * 256 * 256 * 256 + HL * 256 * 256)
        temp = LH + LL + HH + HL

        response.append(temp)

    return response
