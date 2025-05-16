import serial
import struct
import time

# 建構 UART IF 封包 (Command Code + optional payload)
def build_uart_if_packet(cmd_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    length = 4 + len(payload)  # header checksum + data checksum + payload
    header_checksum = 0x0000
    data_checksum = 0x0000
    return struct.pack('>IHHHH', unique_id, cmd_code, length, header_checksum, data_checksum) + payload

# 解析封包內容（簡單印出 UDP Payload）
def parse_response(resp: bytes):
    if not resp or not resp.startswith(bytes.fromhex('d0f9ee5d')):
        return False

    cmd_id = resp[4]
    if cmd_id == 0x08:  # Command 0x0008 對應 UDP Receive
        payload = resp[9:]
        if len(payload) < 20:
            print("⚠️ 封包長度不足")
            return True

        src_ipv6 = ":".join(f"{(payload[i]<<8 | payload[i+1]):04x}" for i in range(0, 16, 2))
        src_port = int.from_bytes(payload[16:18], 'big')
        data = payload[18:]

        print(f"\n📩 來自：[{src_ipv6}]:{src_port}")
        print(f"📦 Payload HEX：{data.hex()}")
        try:
            print(f"🔤 Payload 字串：{data.decode(errors='ignore')}")
        except:
            pass
        return True

    return False

def main():
    ser = serial.Serial(port='COM23', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1)
    print(f"✅ 已連線至 {ser.port}, 開始接收 UDP 封包...\n")

    recv_packet = build_uart_if_packet(0x0002)  # Command 0x0002: Receive UDP packet

    try:
        while True:
            ser.write(recv_packet)
            response = ser.read(128)
            if response:
                parse_response(response)
            time.sleep(1)  # 每秒查一次
    except KeyboardInterrupt:
        print("\n🛑 偵聽中止")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
