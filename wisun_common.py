# wisun_common.py
import struct

def checksum(data: bytes) -> int:
    return sum(data) % 0x10000

def build_packet(cmd: int, payload: bytes = b'') -> bytes:
    uid = 0xD0EA83FC
    length = 4 + len(payload)
    header = struct.pack('>IHH', uid, cmd, length)
    head_chk = checksum(header)
    data_chk = checksum(payload)
    return header + struct.pack('>HH', head_chk, data_chk) + payload
