# This script configures and starts the frontend in PowerShell

# Get the directory of the current script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Construct the path to the frontend directory
$FrontendDir = Join-Path -Path $ScriptDir -ChildPath "frontend"

# Check if the frontend directory exists
if (-not (Test-Path $FrontendDir -PathType Container)) {
    Write-Error "Frontend directory not found at $FrontendDir"
    Exit 1
}

# Change to the frontend directory
Push-Location $FrontendDir

# Check if node_modules directory exists
$NodeModulesDir = Join-Path -Path $FrontendDir -ChildPath "node_modules"

if (-not (Test-Path $NodeModulesDir -PathType Container)) {
    Write-Host "Installing frontend dependencies..."
    # Ensure npm is available
    $npmExists = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmExists) {
        Write-Error "'npm' command not found. Please install Node.js and npm, and ensure they are in your PATH."
        Pop-Location # Return to original directory before exiting
        Exit 1
    }
    npm install
    # Check for errors during npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed with exit code $LASTEXITCODE"
        Pop-Location
        Exit 1
    }
}

Write-Host "Starting frontend..."
# Start the frontend development server (usually non-blocking)
npm start

# Check if npm start failed immediately (optional, depends on how npm start behaves)
if ($LASTEXITCODE -ne 0) {
    Write-Warning "'npm start' might have encountered an issue (exit code $LASTEXITCODE). Check the output above."
}

# Return to the original directory
Pop-Location