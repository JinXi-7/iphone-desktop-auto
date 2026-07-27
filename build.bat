@echo off
chcp 65001 >nul
echo ========================================
echo   一键拨号 - 打包构建
echo ========================================
echo.

cd /d e:\iphone-desktop-auto

echo [1/2] 清理旧构建...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "一键拨号.spec" del "一键拨号.spec"

echo [2/2] 正在打包（可能需要几分钟）...
pyinstaller --name "一键拨号" --windowed --noconfirm ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import "clr_loader" ^
  --hidden-import "pythonnet" ^
  --hidden-import "webview.platforms.edgechromium" ^
  --hidden-import "webview.platforms.winforms" ^
  main.py

if exist "dist\一键拨号\一键拨号.exe" (
    echo.
    echo ========================================
    echo   打包成功！
    echo   输出目录: dist\一键拨号\
    echo   可执行文件: dist\一键拨号\一键拨号.exe
    echo.
    echo   注意: 将 .env 和 contacts_template.xlsx
    echo   复制到 dist\一键拨号\ 目录下
    echo ========================================
) else (
    echo.
    echo 打包失败，请检查错误信息
)

pause
