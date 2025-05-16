import serial
from time import sleep

# 初始化兩個序列埠連線
# bp35c5：連接 ROHM BP35C5（Wi-SUN 模組）
# esp32：連接 ESP32（接收轉發的 binary 封包）
bp35c5 = serial.Serial("COM7", 115200)
esp32 = serial.Serial("COM12", 115200)

# 進入主迴圈持續監聽來自 bp35c5 的資料
while True:
    if bp35c5.in_waiting:
        # 讀取一行資料並去除換行與編碼錯誤
        line = bp35c5.readline().decode('utf-8', errors='ignore').strip()

        # 檢查是否為 Wi-SUN 封包命令行（udpst 或 udprt）
        if "udpst" in line or "udprt" in line:
            try:
                # 擷取最後一段為封包 HEX 字串（通常是指令行的最後一段）
                hex_str = line.split(" ")[-1].strip('"')

                # 將 HEX 字串轉為 binary bytes 格式
                raw_bytes = bytes.fromhex(hex_str)

                # 傳送 binary 資料到 ESP32 的 UART
                esp32.write(raw_bytes)

                
                print("已傳送 binary 給 ESP32:", hex_str)

            except Exception as e:
                
                print("錯誤 HEX 字串，無法轉換:", line)

    sleep(0.01)
