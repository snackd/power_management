import os
import re
import redis

# 使用 Shell Script 指令，找網路介面卡訊息
command = 'ifconfig'
data = os.popen(command)
system_message = data.read()

find_pattern = 'Ethernet'

# 找尋要的片段訊息
find_ethernet = re.findall(find_pattern, system_message)

# 找尋路徑
file_path = "/dev/ttyUSB0"

# 檢查是否存在此路徑
check_path_file = os.path.exists(file_path)

# 如果有找到 Ethernet 的片段訊息
if find_ethernet:
    # deliver_way = 'Ethernet'

r = Redis('localhost')
r.set('deliver_way', 'Ethernet')

# 如果存在此路徑則支援 NB-IoT
elif check_path_file:
    deliver_way = 'NB-IoT'

# 都沒有的結果(暫時)
else:
    deliver_way = 'Ethernet'
