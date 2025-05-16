import serial
import time
import binascii
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

def main():
    ser = serial.Serial(
        port='COM7', baudrate=115200,
        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, timeout=2,
        xonxoff=False, rtscts=False, dsrdtr=False
    )

    pan_id   = 0x1234
    mac = bytes.fromhex('001D12910003EA4A')
    pwd    = b'PASSWORD12345678'
    udp_port = 12345

    try:
        print("🟢 設為 End Device")

        # 0. Reset Hardware + 等 Startup Completion
        send_cmd(ser, 0x00D9, "Reset Hardware")
        time.sleep(5)   # ← 延遲 5 秒，確保模組完成啟動

        # 1. Set Initial Settings → End Device 模式
        send_cmd(ser, 0x005F, "Set Initial Settings", bytes([0x02,0x00,0x04,0x00]))

        send_cmd(ser, 0x0051, "Set Channel", b'\x21')  # 設定為 Channel 33

        # 2. 下發自己的 PANA 認證資訊
        send_cmd(ser, 0x002C, "PANA Auth Info (Self)", mac + pwd)
        assert isinstance(mac + pwd, bytes), "資料不是 bytes 類型"
        assert len(mac + pwd) == 24, "PANA payload 長度錯誤，必須是 24 bytes"

        send_cmd(ser, 0x0013, "Send Join")

        # 3. Initiate HAN Operation
        send_cmd(ser, 0x000A, "Initiate HAN Operation", pan_id.to_bytes(2,'big'))

        # 4. Initiate HAN PANA
        send_cmd(ser, 0x003A, "Initiate HAN PANA")

        # 5. 切到 Initial Connection Mode（開始掃描）
        send_cmd(ser, 0x0025, "Switch to Init Mode", b'\x01')

        # 6. 等 MAC 層連線完成
        raw = wait_notify_data(ser, b'\x60\x1A', timeout=30)
        if not raw: return
        status = raw[12]
        print("✅ MAC 連線完成" if status == 0x01 else f"⚠️ status={status:02X}")

        # 7. 等 PANA 認證完成
        raw = wait_notify_data(ser, b'\x60\x1A', timeout=30)
        if not raw: return
        status = raw[12]
        print("✅ PANA 認證完成" if status == 0x02 else f"⚠️ status={status:02X}")

        # 8. 切回 Normal Mode
        send_cmd(ser, 0x0025, "Switch to Normal Mode", b'\x02')

        # 9. 開 UDP 埠
        send_cmd(ser, 0x0005, "Open UDP Port", udp_port.to_bytes(2,'big'))

        # 10. 傳送測試 UDP
        ipv6 = bytes.fromhex('FE80000000000000000021D12910003EA4')
        msg  = b'Hello A from C'
        payload = ipv6 + len(msg).to_bytes(2,'big') + b'\x01' + msg
        send_cmd(ser, 0x00D1, "Send UDP", payload)

        print("✅ End Device 配對並傳送完成！")

    finally:
        ser.close()

if __name__ == "__main__":
    main()
