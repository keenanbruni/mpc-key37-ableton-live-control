@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LIBRARY=%USERPROFILE%\Documents\Ableton\User Library"
set "SCRIPTS=%LIBRARY%\Remote Scripts"
set "TARGET=%SCRIPTS%\MPC_Key_37"
set "BACKUP="

if not exist "%SCRIPTS%" mkdir "%SCRIPTS%"

if exist "%TARGET%" (
    set "BACKUP=%LIBRARY%\Remote Script Backups\MPC_Key_37-backup-%RANDOM%%RANDOM%"
    if not exist "%LIBRARY%\Remote Script Backups" mkdir "%LIBRARY%\Remote Script Backups"
    move "%TARGET%" "%BACKUP%" >nul
    if errorlevel 1 goto :failed
)

xcopy "%~dp0MPC_Key_37" "%TARGET%\" /E /I /H /Y >nul
if errorlevel 2 goto :restore

if defined BACKUP if exist "%BACKUP%\midi_profile.json" copy /Y "%BACKUP%\midi_profile.json" "%TARGET%\midi_profile.json" >nul

echo.
echo Installed MPC Key 37 Ableton Live Control.
echo Restart Live, then select MPC Key 37 in Settings ^> Tempo ^& MIDI.
if defined BACKUP echo Your previous version is in "%BACKUP%".
goto :done

:restore
if defined BACKUP move "%BACKUP%" "%TARGET%" >nul

:failed
echo.
echo Installation failed. Your previous script was restored when possible.

:done
pause
