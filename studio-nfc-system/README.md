# 工作室 NFC 打卡 + 電腦租借系統

一台 Raspberry Pi 同時提供 7 吋觸控 Kiosk、FastAPI/SQLite 伺服器及 PN532 NFC 讀卡服務。介面為繁體中文，區網內可從其他電腦開啟管理後台。

## 功能與目錄

- `/`：Kiosk 打卡、租借／歸還、四台電腦即時狀態
- `/admin`：即時看板、使用者／綁卡、材料管理、紀錄修正、報表 CSV、電腦維護、稽核與閉店時間
- `/docs`：FastAPI 自動產生的 API 文件
- `app/`：API、SQLite models 及靜態前端
- `services/nfc_reader.py`：PN532 常駐讀卡程式及鍵盤模擬模式
- `systemd/`：API 與 NFC 服務範本
- `data/studio.db`：首次啟動時自動建立（請定期備份）

材料管理內建電阻、電容、電晶體三種分類，可用名稱、規格或存放位置即時搜尋；搜尋欄同時提供可輸入的下拉建議。每項材料可記錄庫存數量、規格、位置及啟用狀態，新增、編輯和停用都會寫入稽核紀錄。

## 前後端資料流

Kiosk 與管理後台皆由 FastAPI 同源提供，不需要 CORS。畫面不含展示用假資料：列表、數量及設備總數皆由 API 取得。管理 API 必須帶登入 Token；公開端僅能感應卡片、借還電腦及讀取設備狀態。

- 使用者：`GET/POST /api/admin/users`、`PUT /api/admin/users/{id}`，停用使用者採狀態更新，避免破壞歷史紀錄。
- NFC：讀卡服務送出 `POST /api/nfc/tap`，後端以 UID 查詢使用者及未結束打卡紀錄，交易完成後透過 `/ws` 推送結果。
- 電腦：`GET /api/computers` 讀取 SQLite 狀態；管理員可透過 `PATCH /api/admin/computers/{id}` 設為可用、維護或離線。
- 租借：`POST /api/rentals` 與 `PATCH /api/rentals/return` 同時更新租借紀錄及電腦狀態；資料庫唯一索引防止同人或同電腦同時存在多筆未歸還紀錄。
- 材料：管理 API 提供列表、單筆、建立、修改及軟刪除，包含 `created_at` 與 `updated_at`；庫存不得小於零。
- 設定／報表／稽核：皆由後端讀寫或聚合 SQLite，CSV 也由後端產生。

材料另分為消耗型與可歸還型。Kiosk 的「材料領用」會先要求 NFC 驗證，後端核發 10 分鐘短效 Session；使用者身份不由前端傳入。每次領用都透過 `POST /api/material-rentals` 在同一交易內扣除庫存、建立 `material_rentals` 紀錄及寫入 audit log。請求包含唯一 `request_id`，重複送出不會再次扣庫存。可歸還型可由本人或管理員歸還並補回庫存，消耗型則保留 `consumed` 歷史紀錄、不提供歸還。

材料領用相關 API：

- `GET /api/materials`：公開讀取可領用材料與後端統一計算的庫存狀態。
- `POST /api/material-session/prepare`：讓下一次 NFC 感應只驗證材料領用身份，不會把已簽到者簽退。
- `POST /api/material-rentals`：短效 Session 驗證後，交易式領用材料。
- `GET /api/material-rentals/mine`：查看本人的材料紀錄。
- `POST /api/material-rentals/{id}/return`：本人歸還可歸還型材料。
- `GET /api/admin/material-rentals`：管理員查看及篩選所有材料領用紀錄。
- `POST /api/admin/material-rentals/{id}/return`：管理員處理歸還。

## 在一般電腦快速啟動

需要 Python 3.11 以上：

```bash
cd studio-nfc-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ADMIN_PASSWORD='你的安全密碼' uvicorn app.main:app --reload --host 0.0.0.0
```

瀏覽 `http://127.0.0.1:8000/`；後台為 `http://127.0.0.1:8000/admin`。初始帳號是 `admin`。若未設定 `ADMIN_PASSWORD`，開發預設密碼是 `change-me-now`，正式使用前務必更換。環境變數只在資料庫首次建立管理員時生效；已建立後可在後台編輯管理員密碼。

沒有 NFC 硬體時，另開終端機：

```bash
source .venv/bin/activate
pip install requests
python services/nfc_reader.py --simulate
```

先在後台新增使用者並填入同一個 UID，或按「綁卡」後於 60 秒內在模擬程式輸入 UID。

## Raspberry Pi 安裝

以下以 Raspberry Pi OS Bookworm、使用者 `pi`、安裝目錄 `/opt/studio-nfc` 為例。如使用者或路徑不同，需同步修改兩個 service 檔。

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip chromium usbutils libusb-1.0-0
sudo mkdir -p /opt/studio-nfc
sudo cp -a . /opt/studio-nfc/
sudo chown -R pi:pi /opt/studio-nfc
cd /opt/studio-nfc
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-nfc.txt
cp .env.example .env
nano .env
```

PN532 建議切至 USB 模式。用 `lsusb` 確認裝置後，先以互動方式測試：

```bash
/opt/studio-nfc/.venv/bin/python services/nfc_reader.py --device usb
```

若走 UART，請在 `raspi-config` 啟用 serial port、停用 login shell，並把 service 的 device 改成適合接線的 nfcpy 路徑（常見為 `tty:S0:pn532`）。裝置權限不足時，將 `pi` 加入 `dialout` 群組；USB 裝置可依 `nfcpy` 文件安裝 udev rule。

## 啟用 systemd

```bash
sudo cp systemd/studio-api.service systemd/studio-nfc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now studio-api.service studio-nfc.service
systemctl status studio-api.service studio-nfc.service
journalctl -u studio-api.service -u studio-nfc.service -f
```

區網管理後台網址是 `http://樹莓派IP:8000/admin`。建議替 Raspberry Pi 設 DHCP 固定租約，並只允許可信任的內網連線；若需跨網際網路存取，應另加 HTTPS reverse proxy、持久化 session 與更完整的存取控管。

## Chromium Kiosk 自動啟動

在 Raspberry Pi OS Desktop 開啟自動登入，建立 `~/.config/autostart/studio-kiosk.desktop`：

```ini
[Desktop Entry]
Type=Application
Name=Studio Kiosk
Exec=chromium --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble http://127.0.0.1:8000/
X-GNOME-Autostart-enabled=true
```

隱藏滑鼠游標可安裝 `unclutter`。若 Chromium 執行檔名稱為 `chromium-browser`，相應替換 `Exec`。觸控螢幕旋轉可在 Raspberry Pi 的 Display Settings 設定。

## 自動結算、備份與時間

後台可設定每日結算時間。服務每 30 秒檢查一次：到時將未簽退紀錄標為 `auto_closed`、未歸還租借標為 `auto_returned`。Raspberry Pi 必須設為正確時區並啟用 NTP：

```bash
sudo timedatectl set-timezone Asia/Taipei
timedatectl status
```

SQLite 在 WAL 以外的簡單部署可停服務後備份：

```bash
sudo systemctl stop studio-api studio-nfc
cp /opt/studio-nfc/data/studio.db /安全的備份位置/studio-$(date +%F).db
sudo systemctl start studio-api studio-nfc
```

## 測試

```bash
source .venv/bin/activate
pytest -q
```

核心測試涵蓋簽到 → 借用 → 阻擋簽退 → 歸還 → 簽退，以及未知卡片處理。
