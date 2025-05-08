@echo off
setlocal enabledelayedexpansion

:: 设置桌面路径和日期变量
set "desktop=%USERPROFILE%\Desktop"
set "timestamp=%date:/=-%_%time::=-%"
set "timestamp=%timestamp: =0%"

:: 1. 打包当前文件夹为ZIP
echo [1/3] 正在打包文件夹...
powershell -Command "$ProgressPreference='SilentlyContinue'; Compress-Archive -Path .\* -DestinationPath '%desktop%\batch_%timestamp:~0,8%.zip' -Force"
if %ERRORLEVEL% neq 0 (
    echo [错误] ZIP打包失败，请检查文件夹权限或空间 > "%desktop%\error_%timestamp%.txt"
    exit /b 1
)

:: 2. 顺序执行Python脚本
echo [2/3] 开始执行Python脚本...
set "scripts=1.py 2.py 3.py 4.py 5.py 6.py 7.py 8.py"

for %%i in (%scripts%) do (
    echo 正在执行 %%i...
    python "%%i" 2>> "%desktop%\error_%timestamp%.txt"
    if !ERRORLEVEL! neq 0 (
        echo [错误] %%i 执行失败，详见日志 >> "%desktop%\%timestamp%.txt"
        echo 错误已记录到桌面 %timestamp%.txt
        exit /b 1
    )
)

:: 3. 完成处理
echo [3/3] 所有脚本执行完成
pause
exit /b 0

:: Ctrl+C中断处理
:handle_ctrlc
echo 用户手动中断！ >> "%desktop%\error_%timestamp%.txt"
echo 操作已中止，错误日志已保存
exit /b 1