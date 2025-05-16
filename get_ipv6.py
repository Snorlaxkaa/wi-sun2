import serial
import struct
import time


def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    data_len = 4 + len(payload)  # header checksum + data checksum + payload
    header_checksum = 0x0000
    data_checksum = 0x0000
    return struct.pack('>IHHHH', unique_id, cmd_code, data_len, header_checksum, data_checksum) + payload

def parse_ipv6_response(resp: bytes):
    if len(resp) < 20 or not resp.startswith(bytes.fromhex('d0f9ee5d')):
        print("⚠️ 無效封包")
        return

    ipv6_bytes = resp[-16:]
    ipv6 = ":".join(f"{(ipv6_bytes[i] << 8 | ipv6_bytes[i+1]):04x}" for i in range(0, 16, 2))
    print(f"🌐 模組 IPv6 位址：{ipv6}")

def main():
    SERIAL_PORT = 'COM5'
    BAUD_RATE = 115200

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 已連線至 {SERIAL_PORT}\n")
    except Exception as e:
        print(f"❌ 開啟串口失敗: {e}")
        return

    # 🔍 查詢 IPv6（0x0003）
    packet = build_uart_if_packet(0x0003)
    print(f"📤 查詢 IPv6 封包 HEX: {packet.hex()}")
    ser.write(packet)
    time.sleep(0.5)

    resp = ser.read(64)
    print(f"📥 回應 HEX: {resp.hex() if resp else '(無回應)'}")
    if resp:
        parse_ipv6_response(resp)
    print()

    # 🔍 查詢 UDP Port 開啟狀態（0x0009）
    packet = build_uart_if_packet(0x0009)
    print(f"📤 查詢 UDP Port 狀態封包 HEX: {packet.hex()}")
    ser.write(packet)
    time.sleep(0.5)

    resp = ser.read(64)
    print(f"📥 回應 HEX: {resp.hex() if resp else '(無回應)'}")

    ser.close()

if __name__ == '__main__':
    main()
