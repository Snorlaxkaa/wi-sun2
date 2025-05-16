import serial
import struct
import time

def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    data_len = 4 + len(payload)
    return struct.pack('>IHHHH', unique_id, cmd_code, data_len, 0x0000, 0x0000) + payload

def parse_channel(resp: bytes):
    if len(resp) >= 11:
        channel = resp[-1]
        print(f"📡 Channel：{channel}")
    else:
        print("⚠️ 無法解析 Channel 回應")

def parse_panid(resp: bytes):
    if len(resp) >= 12:
        panid = int.from_bytes(resp[-2:], 'big')
        print(f"🌐 PAN ID：0x{panid:04X}")
    else:
        print("⚠️ 無法解析 PAN ID 回應")

def parse_aes_key(resp: bytes):
    if len(resp) >= 20:
        key = resp[-16:]
        print(f"🔐 AES 金鑰：{key.hex().upper()}")
    else:
        print("⚠️ 無法解析 AES 金鑰回應")

def send_cmd(ser, cmd_code, desc, parser):
    pkt = build_uart_if_packet(cmd_code)
    print(f"\n📤 查詢 {desc} 封包 HEX: {pkt.hex()}")
    ser.write(pkt)
    time.sleep(0.5)
    resp = ser.read(64)
    print(f"📥 Raw Response HEX: {resp.hex() if resp else '(無回應)'}")
    if resp:
        parser(resp)

def main():
    SERIAL_PORT = 'COM7'  # 請改為要查詢的模組 COM 埠
    BAUD_RATE = 115200

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 已連線至 {SERIAL_PORT}")
    except Exception as e:
        print(f"❌ 開啟串口失敗: {e}")
        return

    send_cmd(ser, 0x0004, "Channel", parse_channel)
    send_cmd(ser, 0x0005, "PAN ID", parse_panid)
    send_cmd(ser, 0x0006, "AES 金鑰", parse_aes_key)

    ser.close()

if __name__ == '__main__':
    main()
