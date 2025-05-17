#include <Arduino.h>
#include "EL.h"
#include <HardwareSerial.h>

// --- ECHONET Lite 初始化（Dummy UDP，只為 EL 物件需求） ---
#include <WiFiUdp.h>
WiFiUDP elUDP;
EL echo(elUDP, {{0x01, 0x33, 0x01}});  // 住宅・設備関連機器／風扇
// --- 繼電器設定 --------------------------------
#define RELAY_PIN   9   // GPIO9, 請依實際接線調整
#define SERIAL_PORT Serial   // USB 連線

// --- 緩衝區 用來累積封包 bytes ---
static uint8_t buf[64];
static size_t  idx = 0;

// --- callback：只處理 EPC=0x80 開關繼電器 ---
bool callback(byte tid[], byte seoj[], byte deoj[],
              byte esv, byte opc, byte epc, byte pdc, byte edt[])
{
  // 把 callback 的判斷條件也改為 0x01, 0x33, 0x01
if (
    (deoj[0] != 0x01 || deoj[1] != 0x33 || deoj[2] != 0x01) ||
    ((esv != EL_SETC) && (esv != EL_SETI)) ||
    epc != 0x80 || pdc != 1
) {
  return false;
}


  if (edt[0]==0x30) {
    digitalWrite(RELAY_PIN, HIGH);
    SERIAL_PORT.println("✅ 繼電器開啟 (0x30)");
    echo.update(0, 0x80, {0x30});
  }
  else if (edt[0]==0x31) {
    digitalWrite(RELAY_PIN, LOW);
    SERIAL_PORT.println("✅ 繼電器關閉 (0x31)");
    echo.update(0, 0x80, {0x31});
  }
  return true;
}

void setup() {
  // 1) Serial for debug & data receive
  SERIAL_PORT.begin(115200);
  while (!SERIAL_PORT) {}

  // 2) Relay pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

 

  SERIAL_PORT.println(" ESP32 ECHONET 啟動");
}

void loop() {
  // 1) 讀 Serial（USB）所有 bytes
  while (SERIAL_PORT.available()) {
    uint8_t b = SERIAL_PORT.read();
    if (idx < sizeof(buf)) buf[idx++] = b;
  }

  // 2) 如果累積至少 14 bytes，就讀 PDC 決定整包長度
  if (idx >= 14) {
    uint8_t pdc = buf[13];
    if (pdc > 32) {
      SERIAL_PORT.println(" PDC 過大，丟棄");
      idx = 0;
      return;
    }
    size_t frame_len = 14 + pdc;
    if (idx >= frame_len) {
      // 3) 解析並呼叫 callback
      byte tid[2]  = {buf[2], buf[3]};
      byte seoj[3] = {buf[4], buf[5], buf[6]};
      byte deoj[3] = {buf[7], buf[8], buf[9]};
      byte esv     = buf[10];
      byte opc     = buf[11];
      byte epc     = buf[12];
      byte edt[32];
      memcpy(edt, buf + 14, pdc);

      // Debug
      SERIAL_PORT.print(" EPC=0x"); SERIAL_PORT.print(epc, HEX);
      SERIAL_PORT.print(" ESV=0x"); SERIAL_PORT.print(esv, HEX);
      SERIAL_PORT.print(" PDC=");  SERIAL_PORT.println(pdc);

      callback(tid, seoj, deoj, esv, opc, epc, pdc, edt);
      idx = 0;
    }
  }
}