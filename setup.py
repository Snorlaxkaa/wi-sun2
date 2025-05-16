import serial
import struct
import time

# 設定 COM port（請根據實際修改）
COORDINATOR_PORT = 'COM7'
END_DEVICE_PORT = 'COM5'

# 共用函式
def calculate_checksum(data: bytes) -> int:
    return sum(data) % 0x10000

def build_uart_packet(command_code: int, payload: bytes = b'') -> bytes:
    unique_id = 0xD0EA83FC
    length = 4 + len(payload)
    header = struct.pack('>IHH', unique_id, command_code, length)
    header_checksum = calculate_checksum(header)
    data_checksum = calculate_checksum(payload)
    packet = header + struct.pack('>HH', header_checksum, data_checksum) + payload
    return packet

def send_and_receive(ser, code, name, payload=b''):
    pkt = build_uart_packet(code, payload)
    print(f"[TX:{name}] {pkt.hex()}")
    ser.write(pkt)
    time.sleep(1.5)
    resp = ser.read_all()
    print(f"[RX:{name}] {resp.hex()}")
    return resp

# 建立序列埠連線
def open_serial(port):
    return serial.Serial(port=port, baudrate=115200, timeout=2)

# 設定 Coordinator 端
def setup_coordinator():
    ser = open_serial(COORDINATOR_PORT)
    print("== COORDINATOR 設定開始 ==")
    send_and_receive(ser, 0x005F, "設為 Coordinator", b'\x00\x00\x00\x00\x01')
    send_and_receive(ser, 0x0051, "設定 Channel", b'\x21')  # Channel 33
    send_and_receive(ser, 0x0006, "執行 Active Scan", b'\x0A\x00\x00\x20\x00\x00\x00\x00\x00\x00')  # 預設 payload
    send_and_receive(ser, 0x0007, "開始 PAN", b'\x00\x00\x12\x34\x00\x00')  # PAN ID: 0x1234
    return ser

# 設定 End Device 端
def setup_end_device():
    ser = open_serial(END_DEVICE_PORT)
    print("== END DEVICE 設定開始 ==")
    send_and_receive(ser, 0x005F, "設為 End Device", b'\x00\x00\x00\x00\x03')
    send_and_receive(ser, 0x0051, "設定 Channel", b'\x21')
    # 設定 AES 金鑰（全 0）
    send_and_receive(ser, 0x002E, "AES Key", b'\x00' * 17)
    # 設定 PANA 認證資訊（MAC 為虛擬值，Pass: PASSWORD12345678）
    mac = b'\x1D\x12\x91\x00\x03\xEA\x9F'
    pwd = b'PASSWORD12345678'
    send_and_receive(ser, 0x002C, "PANA 認證資訊", mac + pwd)
    send_and_receive(ser, 0x0013, "發送 Join", b'\x12\x34')  # PAN ID
    return ser

# 發送 Ping 測試
def send_ping(ser):
    print("== 傳送 PING ==")
    ipv6 = bytes.fromhex('FE80000000000000021D129F00000111')
    payload = ipv6 + b'\x00\x10\x01'
    send_and_receive(ser, 0x00D1, "Send UDP Ping", payload)

# 主流程
if __name__ == '__main__':
    coord_ser = setup_coordinator()
    device_ser = setup_end_device()

    input("請確認 End Device 已成功加入後按下 Enter 鍵以發送 Ping 測試")
    send_ping(device_ser)

    coord_ser.close()
    device_ser.close()
