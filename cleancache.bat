@echo off
title 删除所有 __pycache__ 文件夹
echo 正在搜索并删除 __pycache__ 目录...
echo.

:: 递归查找所有 __pycache__ 目录并删除
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo 删除: %%d
        rmdir /s /q "%%d"
    )
)

echo.
echo 完成！所有 __pycache__ 文件夹已被删除。
pause