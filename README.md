# 一键拨号 (iPhone Desktop Auto)

> 电脑点击，手机自动拨号 -- 局域网 HTTP 直连安卓手机 App，桌面软件一键触发全自动拨号。

[![多平台打包](https://github.com/JinXi-7/iphone-desktop-auto/actions/workflows/build.yml/badge.svg)](https://github.com/JinXi-7/iphone-desktop-auto/actions/workflows/build.yml)

## 下载

从 [GitHub Actions](https://github.com/JinXi-7/iphone-desktop-auto/actions/workflows/build.yml) 下载最新构建产物：

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `一键拨号-windows.zip` | 解压后双击 `一键拨号.exe` |
| macOS | `一键拨号-macos.zip` | 解压后拖到「应用程序」 |
| Linux | `一键拨号-linux.tar.gz` | 解压后终端运行 |
| Android | `一键拨号-android.apk` | 手机安装，允许未知来源 |
| iOS | `一键拨号-ios.zip` | 解压后用 Xcode/AltStore 侧载安装 |

## 功能

- **桌面软件**：打包为独立 `.exe`，双击即用，原生窗口无需浏览器
- **安卓拨号 App**：安装即有 CALL_PHONE 权限，后台前台服务常驻，全自动拨号无需手动确认
- **双模式支持**：App 模式（推荐，HTTP 直连）+ ADB 模式（备用，无线调试）
- **联系人管理**：增删改查联系人，支持分组标记、实时搜索，SQLite 持久化存储
- **一键拨号**：点击联系人或输入号码，手机立即自动拨出
- **Excel 批量导入**：支持 `.xlsx` 格式，自动识别中英文表头，批量导入联系人
- **拨号历史**：自动记录每次拨号的时间、号码、成功/失败状态

## 拨号模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **App 模式（推荐）** | 手机装 App，HTTP 直连，全自动拨号 | 日常使用，企业批量部署 |
| ADB 模式（备用） | 无线调试连接，半自动拨号 | 旧设备或无 App 时备用 |

通过 `.env` 中 `DIAL_MODE=app` 或 `DIAL_MODE=adb` 切换。

## 技术栈

| 组件 | 技术 |
|------|------|
| 桌面窗口 | pywebview 6.2（Edge WebView2） |
| 打包 | PyInstaller 6.21 |
| Web 框架 | Flask 3.0 |
| HTTP 客户端 | requests 2.32（App 模式） |
| 数据库 | SQLite |
| 前端 | Bootstrap 5 + Bootstrap Icons |
| 安卓 App | Kotlin + NanoHTTPD + Foreground Service |
| Excel 导入 | openpyxl 3.1 |

## 环境要求

- Windows 10/11
- Python 3.11（开发用，使用 exe 无需安装 Python）
- 安卓手机 Android 8.0+（安装拨号 App）

## 快速开始

### 方式一：App 模式（推荐）

#### 1. 安装安卓拨号 App

1. 用 Android Studio 打开 `android-app/` 目录
2. 连接手机，点击 Run 构建 APK 并安装
3. 打开 App，授权 CALL_PHONE 权限
4. 点击「启动服务」，记下屏幕显示的 IP 地址

#### 2. 配置桌面端

编辑 `.env` 文件（放在 exe 同目录或项目根目录）：

```ini
DIAL_MODE=app
APP_HOST=手机App显示的IP地址
APP_PORT=8888
```

#### 3. 启动桌面软件

双击 `一键拨号.exe` 或运行 `python main.py`，状态卡片显示绿色「已连接」即可使用。

### 方式二：ADB 模式（备用）

```ini
DIAL_MODE=adb
ADB_DEVICE_IP=10.41.208.158
ADB_DEVICE_PORT=46851
```

需要手机开启无线调试并配对，详见下方「ADB 配置」章节。

## 安卓拨号 App

### App 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ping` | 健康检查，返回设备信息 |
| POST | `/dial` | 拨号请求，参数 `{"phone": "138xxx"}` |
| GET | `/` | 浏览器访问状态页 |

### App 构建

1. 安装 [Android Studio](https://developer.android.com/studio)
2. 打开 `android-app/` 目录
3. 连接手机（开启 USB 调试），点击 Run
4. 或 Build -> Build APK 生成安装包

### App 权限

| 权限 | 用途 |
|------|------|
| CALL_PHONE | 拨打电话（核心功能） |
| INTERNET | HTTP 服务监听 |
| FOREGROUND_SERVICE | 后台服务保活 |
| RECEIVE_BOOT_COMPLETED | 开机自启 |
| POST_NOTIFICATIONS | 前台服务通知（Android 13+） |

## ADB 配置（备用模式）

### 1. 小米17 开启无线调试

1. 设置 -> 我的设备 -> 全部参数与信息 -> 连续点击「OS 版本」7次 -> 开启开发者选项
2. 开发者选项 -> 开启「无线调试」
3. 开发者选项 -> 开启「USB 调试（安全设置）」
4. 点击「使用配对码配对设备」，在 PC 终端执行：

```bash
platform-tools\adb.exe pair IP:配对端口 配对码
```

5. 配对成功后，连接设备：

```bash
platform-tools\adb.exe connect IP:连接端口
```

### 2. 编辑 .env

```ini
DIAL_MODE=adb
ADB_DEVICE_IP=10.41.208.158
ADB_DEVICE_PORT=46851
```

## 打包 exe

```bash
cd e:\iphone-desktop-auto
venv\Scripts\activate
build.bat
```

打包后把 `.env` 和 `contacts_template.xlsx` 复制到 `dist\一键拨号\` 目录下。

> App 模式不需要 `platform-tools/`，exe 体积更小。

## Excel 批量导入

参考 `contacts_template.xlsx` 模板：

| 姓名 | 电话 | 分组 |
|------|------|------|
| 张三 | 13800138000 | 同事 |
| 李四 | 13900139000 | 家人 |

在软件联系人区域点击「导入」按钮上传即可。

表头自动识别：姓名/name/联系人、电话/phone/号码/手机、分组/group/类别。

## 项目结构

```
iphone-desktop-auto/
├── main.py                    # 桌面程序入口（pywebview 窗口）
├── app.py                     # Flask 主程序 + 路由
├── dialer.py                  # 拨号逻辑（App HTTP 模式 + ADB 备用模式）
├── models.py                  # SQLite 数据模型（联系人 + 拨号历史）
├── importer.py                # Excel 批量导入
├── config.py                  # 配置管理（.env，支持双模式）
├── paths.py                   # 路径处理（兼容开发/打包模式）
├── build.bat                  # PyInstaller 打包脚本
├── requirements.txt           # Python 依赖
├── .env.example               # 配置模板
├── contacts_template.xlsx     # Excel 导入模板
├── .gitignore
├── README.md
├── android-app/               # 安卓拨号 App 项目
│   ├── app/
│   │   ├── build.gradle.kts
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── java/com/dialer/
│   │       │   ├── MainActivity.kt     # App 主界面
│   │       │   ├── DialService.kt      # 前台服务 + HTTP 服务器
│   │       │   └── BootReceiver.kt     # 开机自启
│   │       └── res/                    # 布局/颜色/图标资源
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   └── gradle.properties
├── static/
│   └── style.css              # 自定义样式
└── templates/
    └── index.html             # 网页界面
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/status` | 获取连接状态（App 或 ADB 模式） |
| POST | `/api/connect` | 连接设备（App 健康检查 / ADB 连接） |
| POST | `/api/dial` | 触发拨号，参数 `{ "phone": "号码", "contact_id": id, "name": "姓名" }` |
| GET | `/api/contacts?search=` | 获取联系人列表（支持搜索） |
| POST | `/api/contacts` | 添加联系人 |
| PUT | `/api/contacts/<id>` | 更新联系人 |
| DELETE | `/api/contacts/<id>` | 删除联系人 |
| POST | `/api/import` | Excel 批量导入联系人（multipart 上传） |
| GET | `/api/history` | 获取拨号历史记录 |

## 版本

- v1.0.0 - 安卓拨号 App + HTTP 直连模式，全自动拨号，企业级部署
- v0.4.0 - 桌面软件打包（pywebview + PyInstaller），Python 3.11 环境
- v0.3.0 - Excel 批量导入 + 拨号历史记录
- v0.2.0 - 联系人 CRUD + SQLite + 一键拨号（半自动模式）
- v0.1.0 - 项目骨架：Flask 服务 + ADB 状态检测 + 快速拨号
