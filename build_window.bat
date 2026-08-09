@echo off

echo building remote platform

python -m PyInstaller ^
--noconfirm ^
--windowed ^
--onedir ^
--name RemoteLabPlatform ^
main.py

if not exist dist\RemoteLabPlatform\data (
    mkdir dist\RemoteLabPlatform\data
)

if exist data\remote_lab.db (
    copy data\remote_lab.db dist\RemoteLabPlatform\data\remote_lab.db
)

if exist README.md (
    copy README.md dist\RemoteLabPlatform\README.md
)

if exist TEST_RESULTS.md (
    copy TEST_RESULTS.md dist\RemoteLabPlatform\TEST_RESULTS.md
)

echo.
echo Build complete.
echo Look inside dist\RemoteLabPlatform
echo.

pause