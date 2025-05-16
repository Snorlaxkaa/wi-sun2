#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import re
import time

# 串列埠設定（請依實際 COM port 修改）
PORT = 'COM7'
BAUD = 115200

# Request_cmd 映射：請依照 J11 UART IF 規格書補齊完整的命令對應
Request_cmd = {
    'HardReset': bytearray([0x00, 0x19]),
    'InitSetting': bytearray([0x00, 0x03]),
    'ActionStart': bytearray([0x00, 0x0A]),
    'PANAStart': bytearray([0x00, 0x20]),
    'PANAAuthInfoSetting': bytearray([0x00, 0x2C]),
    'ChangeAcceptanceConnectMode': bytearray([0x00, 0x25]),
    'SendPing': bytearray([0x00, 0xD1]),
}

# 初始化串列埠
ser = serial.Serial(PORT, BAUD, timeout=0.1)


def msg_len(data):
    """計算訊息長度 = 4 + 資料長度（2 bytes big-endian）"""
    length = 4 + (len(data) if data else 0)
    return length.to_bytes(2, byteorder='big')


def head_checksum(unique, cmd, msg):
    """計算標頭部檢查碼，溢位至小於 0xFFFF"""
    s = sum(unique) + sum(cmd) + sum(msg)
    while s >= 0x10000:
        s -= 0x10000
    return s.to_bytes(2, byteorder='big')


def data_checksum(data):
    """計算資料部檢查碼，若無資料回傳 0x0000"""
    if data:
        s = sum(data)
        while s >= 0x10000:
            s -= 0x10000
        return s.to_bytes(2, byteorder='big')
    else:
        return b'\x00\x00'


def pkt_parser(rcv):
    """將二進位封包轉為 hex 串列"""
    return re.split('(..)', rcv.hex())[1::2]


def build_packet(unq_type, cmd, data):
    """組成完整 UART IF 封包並印出 hex"""
    unique = bytearray([0xD0, 0xEA, 0x83, 0xFC]) if unq_type == 'Request' \
             else bytearray([0xD0, 0xF9, 0xEE, 0x5D])
    pkt = unique + cmd + msg_len(data) + head_checksum(unique, cmd, msg_len(data)) + data_checksum(data)
    if data:
        pkt += data
    print('Sending Packet :', ' '.join(pkt_parser(pkt)).upper())
    return pkt


def send_cmd(cmd_name, data):
    """發送 Request 命令，並處理 Response/Notify"""
    ser.write(build_packet('Request', Request_cmd[cmd_name], data))
    rcv = ser.readline()
    parsed = pkt_parser(rcv)
    rcv_cmd = parsed[4] + parsed[5]
    # Response = 0x2000 + cmd, Notify = 0x6000 + cmd
    if rcv_cmd == '{:04x}'.format(0x2000 + sum(Request_cmd[cmd_name])):
        print('Response Cmd :', rcv_cmd)
        if len(parsed) >= 12:
            print('Receive Data :', ' '.join(parsed[12:]).upper())
    elif rcv_cmd == '{:04x}'.format(0x6000 + sum(Request_cmd[cmd_name])):
        print('Notify Cmd :', rcv_cmd)
        if len(parsed) >= 12:
            print('Receive Data :', ' '.join(parsed[12:]).upper())
    return parsed


def notify_cmd():
    """專門處理通知命令 (Notify)"""
    raw = ser.readline()
    parsed = pkt_parser(raw)
    print('Notify Packet :', ' '.join(parsed).upper())
    return parsed


def user_cmd(cmd_name, hexstr):
    """支援以 hex 字串（如 'AABBCC'）傳 payload"""
    byte_data = bytearray(int(x, 16) for x in re.split('(..)', hexstr)[1::2]) if hexstr else None
    send_cmd(cmd_name, byte_data)


def hard_reset():
    print('Hardware Resetting...')
    send_cmd('HardReset', None)
    time.sleep(1)


def han_action(parameter):
    send_cmd('ActionStart', parameter)
    time.sleep(3)


def pana_auth(mac, pwd):
    mac_bytes = bytearray(int(x, 16) for x in re.split('(..)', mac)[1::2])
    pwd_bytes = bytearray(ord(c) for c in pwd)
    send_cmd('PANAAuthInfoSetting', mac_bytes + pwd_bytes)


def device_setup(mode):
    print('=== Device Setup Start ===')
    hard_reset()
    print('> Init Setting')
    if mode in ('a', 'b', 'c'):
        init_param = {'a': b'\x01\x00\x10\x00', 'b': b'\x02\x00\x10\x00', 'c': b'\x03\x00\x10\x00'}[mode]
        send_cmd('InitSetting', init_param)
    print('> HAN Action Start')
    han_action(b'\xCA\xFE' if mode == 'a' else b'\xFF' * 8)

    if mode == 'a':
        send_cmd('PANAStart', None)
        mac = input('Enter MAC Address: ')
        pwd = input('Enter PANA Password: ')
        pana_auth(mac, pwd)
    else:
        pana_auth('', '0123456789abcdef')
        send_cmd('PANAStart', None)
        time.sleep(1)
        r = notify_cmd()
        if r[12] == '01':
            print('Auth Dest :', r[13:])
    if mode in ('a', 'b'):
        m = input('Select HAN mode (01=init,02=norm): ')
        send_cmd('ChangeAcceptanceConnectMode', int(m, 16).to_bytes(1, 'big'))
    print('=== Device Setup Complete ===\n')


def main():
    print(f'Wi-SUN Port: {PORT} @ {BAUD}bps\n')
    mode = input('Enter Machine Mode (a/b/c): ').strip()
    device_setup(mode)
    while True:
        cmd = input('Enter Cmd Name: ').strip()
        data = input('Enter payload hex (or leave blank): ').strip()
        user_cmd(cmd, data)
        time.sleep(2)
        while ser.in_waiting:
            notify_cmd()


if __name__ == '__main__':
    main()
