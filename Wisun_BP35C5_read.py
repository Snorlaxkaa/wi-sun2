import serial
from time import sleep

bp35c5 = serial.Serial("COM7", 115200)
esp32 = serial.Serial("COM12", 115200)

while True:
    if bp35c5.in_waiting:
        line = bp35c5.readline().decode('utf-8', errors='ignore').strip()

        if "udpst" in line or "udprt" in line:
            # 嘗試擷取封包 HEX
            try:
                hex_str = line.split(" ")[-1].strip('"')
                raw_bytes = bytes.fromhex(hex_str)
                esp32.write(raw_bytes)
                print("✅ 傳送 binary 給 ESP32:", hex_str)
            except Exception as e:
                print("❌ 錯誤 HEX 字串，無法轉換:", line)
    sleep(0.01)
