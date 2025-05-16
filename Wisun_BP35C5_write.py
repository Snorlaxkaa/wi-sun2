# -*- coding: utf-8 -*-
import serial
import binascii

# 初始化串列埠
ser = serial.Serial("COM5", 115200)  # 依實際使用 COM port 調整

def build_echonet_frame(deoj, esv, epc, edt):
    """
    根據使用者輸入組成完整 ECHONET Lite 封包（HEX 字串）
    """
    data_format = {
        'EHD':  '1081',
        'TID':  '0001',
        'SEOJ': '05FF01',
        'DEOJ': deoj,
        'ESV':  esv,
        'OPC':  '01',
        'EPC':  epc,
        'PDC':  f"{len(edt) // 2:02X}",
        'EDT':  edt.upper()
    }

    frame = ''
    for key in ['EHD', 'TID', 'SEOJ', 'DEOJ', 'ESV', 'OPC', 'EPC', 'PDC', 'EDT']:
        frame += data_format[key]
    return frame
33
while True:
    print("\n=== ECHONET Lite UART 傳送器 ===")
    deoj = input("請輸入 DEOJ (如 029001): ").strip()
    esv  = input("請輸入 ESV  (如 61=SetC): ").strip()
    epc  = input("請輸入 EPC  (如 B6=鎖控制): ").strip()
    edt  = input("請輸入 EDT  (如 41=解鎖, 42=上鎖): ").strip()

    try:
        # 組出封包 HEX 字串
        hex_frame = build_echonet_frame(deoj, esv, epc, edt)
        print(f"📦 封包 HEX: {hex_frame}")

        # 組成 UDP 命令格式：udpst IP PORT HEX
        cmd_str = f"udpst 2001:db8::2 20171 {hex_frame}\n"
        print(f"📤 傳送指令: {cmd_str.strip()}")

        # 寫入串列埠
        ser.write(cmd_str.encode())

    except Exception as e:
        print(f"❌ 發送錯誤：{e}")
