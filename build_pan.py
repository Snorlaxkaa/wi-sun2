import serial  
import struct  
import time

def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:  
    unique_id = 0xD0EA83FC  
    data_len = 4 + len(payload)  
    return struct.pack('>IHHHH', unique_id, cmd_code, data_len, 0x0000, 0x0000) + payload

def parse_event_response(resp: bytes):  
    if not resp or len(resp) < 8 or not resp.startswith(bytes.fromhex('d0f9ee5d')):  
        return  
    cmd_id = resp[4]  
    sub_cmd = resp[5]  
    if cmd_id == 0x20:  
        if sub_cmd == 0x01:  
            print("📡 掃描事件（SubCmd: 01）")  
        elif sub_cmd == 0x07:  
            print("🎉 有模組嘗試 Join（SubCmd: 07）")  
        elif sub_cmd == 0x03:  
            print("✅ Join 完成並分配 IPv6（SubCmd: 03）")  
        elif sub_cmd == 0x08:  
            print("📩 收到 UDP 封包通知（SubCmd: 08）")  
        elif sub_cmd == 0x09:  
            print("📢 PAN 建立完成（SubCmd: 09）")  
        else:  
            print(f"⚠️ 未知子事件通知 CmdID: 0x20 SubCmd: {sub_cmd:02X}")  
    else:  
        print(f"⚠️ 其他未知 CmdID: {cmd_id:02X}")

def main():  
    SERIAL_PORT = 'COM5'  # ⬅️ 修改成您的模組 B 串口  
    BAUD_RATE = 115200

    try:  
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)  
        print(f"✅ 已連線至 {ser.port}\n")  
    except Exception as e:  
        print(f"❌ 串口開啟失敗: {e}")  
        return

    pkt = build_uart_if_packet(0x0051)
    print(f"📤 執行 Active Scan 封包 HEX: {pkt.hex()}")  
    ser.write(pkt)  
    time.sleep(1)  
    resp = ser.read(128)  
    print(f"📥 回應 HEX: {resp.hex() if resp else '(無回應)'}")  
    print("✅ Active Scan 完成\n")
        # 建立 PAN  
    pkt = build_uart_if_packet(0x0009, bytes([33]))  # 將頻道設為 33
    print(f"📤 建立 PAN 封包 HEX: {pkt.hex()}")  
    ser.write(pkt)  
    time.sleep(0.5)  
    resp = ser.read(128)  
    print(f"📥 回應 HEX: {resp.hex() if resp else '(無回應)'}")  
    print("✅ PAN 建立完成")

    # Initiate HAN PANA
    pkt = build_uart_if_packet(0x0013)
    ser.write(pkt)
    time.sleep(0.3)
    print("🚀 發送 Initiate HAN PANA 指令")

    # 切換為 Initial Connection Mode（允許加入）
    pkt = build_uart_if_packet(0x0025, b'\x01')
    ser.write(pkt)
    time.sleep(0.3)
    print("✅ 已切換為 Initial Connection Mode（允許加入）")


    # 持續輪詢事件  
    try:  
        print("\n🔍 正在接收事件通知中...\n")  
        while True:  
            ser.write(build_uart_if_packet(0x0001))  
            resp = ser.read(128)  
            parse_event_response(resp)  
            time.sleep(1)  
    except KeyboardInterrupt:  
        print("\n🛑 已中止 PAN 維持")  
    finally:  
        ser.close()

if __name__ == '__main__':  
    main()