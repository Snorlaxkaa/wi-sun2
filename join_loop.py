import serial
import struct
import time

def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    data_len = 4 + len(payload)
    return struct.pack('>IHHHH', unique_id, cmd_code, data_len, 0x0000, 0x0000) + payload

def parse_join_response(resp: bytes):
    if not resp or len(resp) < 8:
        return False, "⚠️ 無資料或封包太短"
    if not resp.startswith(bytes.fromhex('d0f9ee5d')):
        return False, "⚠️ 封包不是 Wi-SUN Binary 格式"

    cmd_id = resp[4]
    sub_cmd = resp[5]

    if cmd_id == 0x20 and sub_cmd == 0x07:
        return False, "⌛ 正在進行 PANA Join 中..."
    elif cmd_id == 0x20 and sub_cmd == 0x03:
        return True, "✅ Join 成功，模組已分配 IPv6！"
    elif cmd_id == 0xff:
        return False, "❌ 發生錯誤（0xFFFF 回應）"
    else:
        return False, f"⚠️ 未知回應 CmdID: 0x{cmd_id:02X}, SubCmd: 0x{sub_cmd:02X}"

def main():
    SERIAL_PORT = 'COM7'  # 模組 A 的埠
    BAUD_RATE = 115200

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 已連線至 {SERIAL_PORT}\n")
    except Exception as e:
        print(f"❌ 串口開啟失敗: {e}")
        return

    join_packet = build_uart_if_packet(0x0007)

    while True:
        print("📤 發送 Join 指令...")
        ser.write(join_packet)
        time.sleep(0.5)
        resp = ser.read(64)
        print(f"📥 Raw HEX: {resp.hex() if resp else '(無回應)'}")
        success, message = parse_join_response(resp)
        print(message + "\n")
        if success:
            break
        time.sleep(3)

    ser.close()
    print("🔚 Join 流程結束")

if __name__ == '__main__':
    main()
