import serial
import struct
import time

def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    data_len = 4 + len(payload)  # header checksum + data checksum + payload
    header_checksum = 0x0000
    data_checksum = 0x0000
    return struct.pack('>IHHHH', unique_id, cmd_code, data_len, header_checksum, data_checksum) + payload

def parse_join_response(resp: bytes):
    if not resp or len(resp) < 8:
        print("⚠️ 沒有收到資料或封包太短")
        return

    print(f"📥 Raw Response HEX: {resp.hex()}")

    if not resp.startswith(bytes.fromhex('d0f9ee5d')):
        print("⚠️ 封包開頭錯誤（不是 Wi-SUN Binary 格式）")
        return

    cmd_id = resp[4]
    if cmd_id == 0x20 and resp[5] == 0x07:
        print("✅ Join 指令送出成功，模組正在嘗試加入 PAN")
    elif cmd_id == 0x07:
        print("✅ Join 成功，模組已加入 PAN")
    elif cmd_id == 0xff:
        print("❌ Join 發生錯誤（Command ID: 0xFFFF）")
    else:
        print(f"ℹ️ 收到未知指令回應 CmdID: {cmd_id:02x}")

def main():
    SERIAL_PORT = 'COM7'  # 請改為模組 A 的 COM 埠
    BAUD_RATE = 115200

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 已連線至 {SERIAL_PORT}\n")
    except Exception as e:
        print(f"❌ 串口開啟失敗: {e}")
        return

    # Command 0x0007 = Join，無 payload
    packet = build_uart_if_packet(0x0007)
    print(f"📤 Join 封包 HEX: {packet.hex()}")
    ser.write(packet)

    time.sleep(0.5)
    resp = ser.read(64)

    # 🔍 印出原始 HEX
    print(f"📥 Raw Response HEX: {resp.hex() if resp else '(無回應)'}")

    # 🧠 解析回應內容
    parse_join_response(resp)

    ser.close()

if __name__ == '__main__':
    main()
