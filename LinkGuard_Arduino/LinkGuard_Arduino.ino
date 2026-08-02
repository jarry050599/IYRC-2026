// 12V 四線 RGB LED 燈條控制
//
// 燈條接線（依照片與常見線色判斷）：
//   白線：12V 電源正極（共陽極）
//   紅線：紅色通道，接紅色 MOSFET 的 Drain
//   綠線：綠色通道，接綠色 MOSFET 的 Drain
//   藍線：藍色通道，接藍色 MOSFET 的 Drain
//
// 每個 Arduino PWM 腳位需經電阻連到邏輯等級 N-MOSFET 的 Gate，
// MOSFET Source 接 12V 電源負極，Arduino GND 也要接電源負極（共地）。
// 請勿將 12V 或燈條直接接到 Arduino 的輸出腳位。

// 依實際燈條接線：D5 為紅色通道，D6 為綠色通道。
const byte RED_PIN = 5;
const byte GREEN_PIN = 6;
const byte BLUE_PIN = 3;

void setup() {
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  // 開機時先關閉所有通道。
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  // D5 通道測試 2 秒。
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(RED_PIN, HIGH);
  delay(2000);
  digitalWrite(RED_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  delay(300);

  // D6 通道測試 2 秒。
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(GREEN_PIN, HIGH);
  delay(2000);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  delay(300);

  // D3 通道測試 2 秒。
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(BLUE_PIN, HIGH);
  delay(2000);
  digitalWrite(BLUE_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);

  // 全部關閉 1 秒後重複測試。
  delay(1000);
}
