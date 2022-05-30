# 電壓 Voltage (V)
# 電流 Current (I)
# 頻率 Frequency (F)

t = 10
h = 100
k = 1000

# 轉換單位
def pm210_unit(data_list):
    data_list[0] = data_list[0] / t  # A 相電壓 (Vr) 單位:0.1 V 轉 V
    data_list[1] = data_list[1] / t  # B 相電壓 (Vs) 單位:0.1 V 轉 V
    data_list[2] = data_list[2] / t  # C 相電壓 (Vt) 單位:0.1 V 轉 V

    data_list[3] = data_list[3] / t  # A-B 線電壓 (Vrs) 單位:0.1 V 轉 V
    data_list[4] = data_list[4] / t  # B-C 線電壓 (Vst) 單位:0.1 V 轉 V
    data_list[5] = data_list[5] / t  # C-A 線電壓 (Vtr) 單位:0.1 V 轉 V

    data_list[6] = data_list[6] / k  # A 相電流 (Ir) 單位:0.001 A 轉 A
    data_list[7] = data_list[7] / k  # B 相電流 (Is) 單位:0.001 A 轉 A
    data_list[8] = data_list[8] / k  # C 相電流 (It) 單位:0.001 A 轉 A

    data_list[9] = data_list[9]    # P (合相 P) 功率 單位:W
    data_list[10] = data_list[10]  # Q (合相 Q) 虛功率 單位:VAr
    data_list[11] = data_list[11]  # S (合相 S) 視在功率  單位:VA

    data_list[12] = data_list[12] / t  # F 頻率 (Hz) 單位:0.1 Hz 轉 Hz
    data_list[13] = data_list[13] / k  # PF (合相 PF) 功率因數 單位:0.001 轉 1
    data_list[14] = data_list[14] / h  # EP (合相 EP) 電度 單位:0.01 kWh 轉 kWh

    data_list[15] = data_list[15] / h  # EQ (合相 EQ) 虛功電度 單位:0.01 kVArh轉kVArh
    data_list[16] = data_list[16] / t  # Pd15 (BD15) 15 分鐘需量 單位:0.1 W 轉 W
    data_list[17] = data_list[17] / t  # Pd1 (BD1) 1 分鐘需量 單位:0.1 W 轉 W

    # GEP 發電機電度
    # GEQ 發電機虛功電度

    return data_list