import serial
import time
import binascii
import ipaddress
from wisun_common import build_packet

def send_cmd(ser, cmd: int, desc: str, payload: bytes = b'') -> bytes:
    print(f"🧪 payload before build_packet = {payload.hex().upper()} (len={len(payload)})")
    pkt = build_packet(cmd, payload)
    print(f"[TX:{desc}] {pkt.hex().upper()}")
    ser.write(pkt)
    time.sleep(1.5)
    resp = ser.read(256)
    print(f"[RX:{desc}] {resp.hex().upper()}")
    return resp

def wait_notify_data(ser, code: bytes, timeout: float = 30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        data = ser.read(256)
        if code in data:
            print(f"🔔 收到 Notify({code.hex().upper()})，raw={data.hex().upper()}")
            return data
    print(f"⚠️ 等不到 Notify({code.hex().upper()})")
    return None

def compress_ipv6(resp: bytes) -> str:
    idx = resp.find(b'\xfe\x80')
    raw = resp[idx:idx+16]
    return str(ipaddress.IPv6Address(raw))

def main():
    ser = serial.Serial(
        port='COM5', baudrate=115200,
        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, timeout=2,
        xonxoff=False, rtscts=False, dsrdtr=False
    )

    mac_C = bytes.fromhex('001D12910003EA4A')
    pwd    = b'PASSWORD12345678'
    pan_id   = 0x1234
    udp_port = 12345

    try:
        # 0. Reset Hardware + 等待 Startup Completion (0x6019)
        send_cmd(ser, 0x00D9, "Reset Hardware")
        time.sleep(5)   # ← 延遲 5 秒，確保模組完成啟動

        # 1. Set Initial Settings → Coordinator 模式
        send_cmd(ser, 0x005F, "Set Initial Settings", bytes([0x01,0x00,0x04,0x00]))

        send_cmd(ser, 0x0051, "Set Channel", b'\x21')  # 設定為 Channel 33
        
        send_cmd(ser, 0x002E, "Set AES Key", b'\x00' * 17)  # AES = 17 bytes，全 0

        # 2. 下發 End Device 的 PANA 認證資訊
        send_cmd(ser, 0x002C, "PANA Auth Info (C)", mac_C + pwd)

        # 3. Initiate HAN Operation (PAN ID)
        send_cmd(ser, 0x000A, "Initiate HAN Operation", pan_id.to_bytes(2,'big'))

        # 4. Initiate HAN PANA
        send_cmd(ser, 0x003A, "Initiate HAN PANA")

        # 5. 切到 Initial Connection Mode → 廣播 Enhanced Beacon
        send_cmd(ser, 0x0025, "Switch to Init Mode", b'\x01')

        # 6. 等 MAC 層連線完成 (Notify 0x601A, status=0x01)
        raw = wait_notify_data(ser, b'\x60\x1A', timeout=30)
        if not raw: return
        status = raw[12]
        print("✅ MAC 連線完成" if status == 0x01 else f"⚠️ Unexpected status={status:02X}")

        # 7. 等 PANA 認證完成 (Notify 0x601A, status=0x02)
        raw = wait_notify_data(ser, b'\x60\x1A', timeout=30)
        if not raw: return
        status = raw[12]
        print("✅ PANA 認證完成" if status == 0x02 else f"⚠️ Unexpected status={status:02X}")

        # 8. 切回 Normal Mode
        send_cmd(ser, 0x0025, "Switch to Normal Mode", b'\x02')

        # 9. 開 UDP 埠
        send_cmd(ser, 0x0005, "Open UDP Port", udp_port.to_bytes(2,'big'))

        # 10. 查詢自身 IPv6（可選）
        resp = send_cmd(ser, 0x0009, "Get IP Address")
        ipv6 = compress_ipv6(resp)
        print(f"📍 Coordinator IPv6：{ipv6}")

        # 11. 等待並顯示來自 End Device 的 UDP 訊息
        print("⏳ 等待 UDP Notify…")
        t0 = time.time()
        while time.time() - t0 < 60:
            data = ser.read(256)
            if b'\x60\x18' in data:
                print(f"🔔 收到 UDP Notify：{data.hex().upper()}")
                payload = data[20:]
                try: print("💬 UDP Payload：", payload.decode())
                except: print("⚠️ UDP Payload raw：", payload.hex().upper())
                break

    finally:
        ser.close()

if __name__ == "__main__":
    main()
