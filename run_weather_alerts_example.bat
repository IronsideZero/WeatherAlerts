@echo off
setlocal

REM Set working directory to your project root
cd /d PATH_TO_YOUR_APP_PARENT_DIRECTORY_HERE

REM Start Docker Desktop if not already running
tasklist /FI "IMAGENAME eq Docker Desktop.exe" | find /I "Docker Desktop.exe" >nul
if errorlevel 1 (
    echo Starting Docker Desktop...
    start "" "PATH_TO_YOUR_DOCKER_DESKTOP_EXECUTABLE_HERE"
    
    REM Wait for Docker to become available (up to 60 seconds)
    set DOCKER_STARTED=false
    for /L %%i in (1,1,60) do (
        docker info >nul 2>&1
        if not errorlevel 1 (
            set DOCKER_STARTED=true
            echo Docker is ready.
            goto :runcontainer
        )
        timeout /t 1 >nul
    )
    
    echo Docker failed to start within timeout.
    exit /b 1
)

:runcontainer
echo Building Docker image...
docker build -t weather_alerts .

echo Running Docker container...
docker run --rm --name weather_alerts_container weather_alerts

REM Optional: shut down Docker Desktop
echo Stopping Docker Desktop...
taskkill /IM "Docker Desktop.exe" /F >nul 2>&1

echo Done.
pause
exit /b
