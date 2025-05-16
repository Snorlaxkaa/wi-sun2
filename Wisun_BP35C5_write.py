import serial
import binascii


ser = serial.Serial("COM5", 115200)  # 將此處 "COM5" 改為實際使用的 COM 埠

def build_echonet_frame(deoj, esv, epc, edt):
    """
    根據參數建立一個符合 ECHONET Lite 規範的封包格式。
    封包內容包含標頭、來源/目標物件、服務、屬性等。
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

    # 將所有欄位依序串接成一個完整封包 HEX 字串
    frame = ''
    for key in ['EHD', 'TID', 'SEOJ', 'DEOJ', 'ESV', 'OPC', 'EPC', 'PDC', 'EDT']:
        frame += data_format[key]
    return frame


# 主迴圈：反覆要求使用者輸入封包欄位，並透過 UART 傳送
while True:
    print("\n=== ECHONET Lite UART 傳送器 ===")

    # 由使用者輸入目標設備、服務、屬性與資料
    deoj = input("請輸入 DEOJ (如 013301): ").strip()  # 目標設備，如電風扇 013301
    esv  = input("請輸入 ESV  (如 61=SetC): ").strip()  # 命令型態，如 SetC
    epc  = input("請輸入 EPC  (如 80=開關): ").strip()   # 欲控制的屬性，如 0x80 是電源開關
    edt  = input("請輸入 EDT  (如 30=開, 31=關): ").strip()  # 具體控制數值，如 ON=30，OFF=31

    try:
        # 將輸入資料轉成 HEX 封包格式
        hex_frame = build_echonet_frame(deoj, esv, epc, edt)
        print(f"封包 HEX: {hex_frame}")

        # 組合為透過 Wi-SUN 模組傳送的 UDP 命令格式
        cmd_str = f"udpst 2001:db8::2 20171 {hex_frame}\n"
        print(f"傳送指令: {cmd_str.strip()}")

        # 傳送指令至 UART
        ser.write(cmd_str.encode())

    except Exception as e:
        print(f"發送錯誤：{e}")
