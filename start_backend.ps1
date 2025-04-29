# Support Buddy - Backend Startup Script (PowerShell for Windows)
# This script starts Docker services and the FastAPI backend server

$ErrorActionPreference = 'Stop'  # Exit immediately if a command fails

Write-Host "===== Support Buddy Backend Setup ====="

# Define directories
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path -Path $ScriptRoot -ChildPath "backend"
$DataDir = Join-Path -Path $BackendDir -ChildPath "data"
$VectorDbDir = Join-Path -Path $DataDir -ChildPath "chroma"

# Start Docker Compose services
Write-Host "Starting Docker Compose services..."
docker compose up -d chroma postgres jira confluence-postgres confluence

# Wait for ChromaDB to be healthy
Write-Host "Waiting for ChromaDB to be healthy..."
$ChromaUrl = "http://localhost:8000/api/v2/heartbeat"
while ($true) {
    try {
        $response = Invoke-WebRequest -Uri $ChromaUrl -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "ChromaDB is healthy!"
            break
        }
    } catch {
        Write-Host "Waiting for ChromaDB... ($($_.Exception.Message))"
    }
    Start-Sleep -Seconds 5
}

# Load environment variables if .env exists
$EnvFilePath = Join-Path -Path $BackendDir -ChildPath ".env"
if (Test-Path $EnvFilePath) {
    Write-Host "Loading environment variables from .env..."
    Get-Content $EnvFilePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and !$line.StartsWith('#')) {
            $parts = $line -split '=', 2
            if ($parts.Length -eq 2) {
                $key = $parts[0].Trim()
                $value = $parts[1].Trim().Trim('"').Trim("'") # Remove potential quotes
                # Set environment variable directly in the current process scope
                [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
                # Write-Host "Set env var: $key=$value"
            }
        }
    }
}

# Set default values for Jira credentials if not provided
if (-not $env:JIRA_USER) { $env:JIRA_USER = "admin" }
if (-not $env:JIRA_PASS) { $env:JIRA_PASS = "admin" }

# Verify Jira credentials before attempting connection
Write-Host "Using Jira Credentials - User: '$($env:JIRA_USER)' Pass: $(if ($env:JIRA_PASS) {'****'} else {'(Not Set)'})"

# Wait for Jira to be ready
Write-Host "Waiting for Jira to be ready..."
Start-Sleep -Seconds 10 # Initial wait time
$MaxRetries = 30
$RetryCount = 0
$JiraUrl = "http://localhost:9090/rest/api/2/serverInfo"

while ($RetryCount -lt $MaxRetries) {
    $RetryCount++
    $StatusCode = $null
    $ResponseBody = $null
    try {
        # Manually construct Basic Auth header
        $AuthString = "$($env:JIRA_USER):$($env:JIRA_PASS)"
        $Base64Auth = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($AuthString))
        $AuthHeader = "Basic $Base64Auth"

        # Use Invoke-WebRequest with manual header
        $response = Invoke-WebRequest -Uri $JiraUrl -Headers @{Authorization = $AuthHeader} -Method Get -UseBasicParsing -ErrorAction SilentlyContinue
        $StatusCode = $response.StatusCode

        if ($StatusCode -eq 200) {
            # Optionally, parse $response.Content if needed to verify readiness further
            # $ServerInfo = $response.Content | ConvertFrom-Json
            # if ($ServerInfo.serverTitle) { ... }
            Write-Host "Jira is ready and authenticated! (HTTP $StatusCode)"
            break
        } else {
            # Handle non-200 status codes explicitly if needed, otherwise fall through to catch
            Write-Warning "Received non-200 status from Jira: HTTP $StatusCode"
            # If the status code indicates a specific startup phase (like 503), handle it here or let the catch block handle it.
            if ($StatusCode -eq 503) {
                 Write-Host "Jira is still starting up (HTTP 503)..."
            } elseif ($StatusCode -eq 401) {
                 Write-Error "Error: Authentication failed (HTTP 401). Please check JIRA_USER and JIRA_PASS environment variables."
                 break # Break the loop on auth failure
            } elseif ($StatusCode -eq 403) {
                 Write-Error "Error: Forbidden (HTTP 403). Please check JIRA permissions."
                 break
            } elseif ($StatusCode -eq 404) {
                 Write-Error "Error: Jira API endpoint not found (HTTP 404). Please check if Jira is properly installed and the URL '$JiraUrl' is correct."
                 break
            } else {
                 # Log unexpected non-200 status codes before retrying
                 Write-Warning "Unexpected response status (HTTP $StatusCode)."
            }
        }
    } catch [System.Net.WebException] {
        $StatusCode = [int]$_.Exception.Response.StatusCode
        $ResponseBody = $_.Exception.Response | Get-Content -Raw

        switch ($StatusCode) {
            401 {
                Write-Error "Error: Authentication failed (HTTP 401). Please check JIRA_USER and JIRA_PASS environment variables."
                # Exit 1 # Optionally exit
                break # Break the loop on auth failure
            }
            403 {
                Write-Error "Error: Forbidden (HTTP 403). Please check JIRA permissions."
                # Exit 1 # Optionally exit
                break # Break the loop on auth failure
            }
            404 {
                Write-Error "Error: Jira API endpoint not found (HTTP 404). Please check if Jira is properly installed and the URL '$JiraUrl' is correct."
                # Exit 1 # Optionally exit
                break # Break the loop
            }
            503 {
                Write-Host "Jira is still starting up (HTTP 503)..."
            }
            default {
                Write-Warning "Unexpected response (HTTP $StatusCode). Response: $ResponseBody"
            }
        }
    } catch {
        # Catch other potential errors (network, etc.)
        Write-Warning "An unexpected error occurred while checking Jira: $($_.Exception.Message)"
    }

    if ($RetryCount -lt $MaxRetries) {
        Write-Host "Retrying in 10 seconds... (Attempt $RetryCount/$MaxRetries)"
        Start-Sleep -Seconds 10
    }
}

if ($RetryCount -eq $MaxRetries) {
    Write-Error "Error: Jira failed to start after $MaxRetries attempts."
    Write-Host "Please check:
    1. Docker containers are running (docker ps)
    2. Jira credentials are correct
    3. Jira is running on port 9090"
    Exit 1
}

# Wait for Confluence to be ready
Write-Host "Waiting for Confluence to be ready..."
Start-Sleep -Seconds 10 # Initial wait time
$MaxRetries = 30
$RetryCount = 0
$ConfluenceUrl = "http://localhost:8090/status"

while ($RetryCount -lt $MaxRetries) {
    $RetryCount++
    $State = $null
    try {
        $response = Invoke-RestMethod -Uri $ConfluenceUrl -Method Get
        $State = $response.state # Assuming the response is JSON with a 'state' property

        if ($State -eq "RUNNING") {
            Write-Host "Confluence is ready and running!"
            break
        } elseif ($State -eq "FAILED" -or $State -eq "ERROR") {
            Write-Warning "Confluence state is $State. Restarting confluence container..."
            docker compose restart confluence
            Write-Host "Waiting 15 seconds for Confluence to restart..."
            Start-Sleep -Seconds 15
        } else {
            Write-Host "Confluence is still starting up or in unknown state: $State"
        }
    } catch {
        Write-Warning "Failed to get Confluence status: $($_.Exception.Message)"
    }

    if ($RetryCount -lt $MaxRetries) {
        Write-Host "Retrying in 10 seconds... (Attempt $RetryCount/$MaxRetries)"
        Start-Sleep -Seconds 10
    }
}

if ($RetryCount -eq $MaxRetries) {
    Write-Error "Error: Confluence failed to reach RUNNING state after $MaxRetries attempts."
    Write-Host "Please check:
    1. Docker containers are running (docker ps)
    2. Confluence is running on port 8090"
    Exit 1
}

# Check if Python is installed
$pythonExists = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExists) {
    $python3Exists = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $python3Exists) {
        Write-Error "Error: Python (python or python3) is not installed or not in PATH. Please install Python and try again."
        Exit 1
    } else {
        $PythonExe = "python3"
    }
} else {
     $PythonExe = "python"
}
Write-Host "Using Python executable: $PythonExe"

# Change to backend directory
Push-Location $BackendDir

# Check if 'uv' command exists, if not, provide instructions
$uvExists = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvExists) {
    Write-Warning "'uv' command not found. Attempting to install using winget..."
    try {
        winget install --id astral-sh.uv --accept-package-agreements --accept-source-agreements -e
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Error: Failed to install 'uv' using winget (Exit Code: $LASTEXITCODE). Please install it manually and ensure it's in your PATH."
            Write-Host "You can try: pipx install uv  OR  $PythonExe -m pip install uv"
            Exit 1
        }
        Write-Host "'uv' installed successfully via winget. Please restart the windows terminal and ide or ensure the PATH is updated in this session if needed."
        # Re-check if uv is now available after installation
        $uvExists = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uvExists) {
            Write-Error "Error: 'uv' command still not found after winget installation. Please check your PATH or install manually."
            Exit 1
        }
        Write-Host "'uv' command is now available."
    } catch {
        Write-Error "An error occurred during winget installation: $($_.Exception.Message)"
        Write-Host "Please install 'uv' manually and ensure it's in your PATH."
        Write-Host "You can try: pipx install uv  OR  $PythonExe -m pip install uv"
        Exit 1
    }
}

# Install dependencies (in backend dir)
Write-Host "Installing dependencies using uv..."
uv sync

# Activate virtual environment
$VenvActivateScript = Join-Path -Path ".\.venv" -ChildPath "Scripts\Activate.ps1"
if (Test-Path $VenvActivateScript) {
    Write-Host "Activating virtual environment..."
    . $VenvActivateScript
} else {
    Write-Warning "Virtual environment activation script not found at $VenvActivateScript. Skipping activation."
    Write-Warning "Make sure the virtual environment exists and was created correctly."
}

# Create necessary directories
Write-Host "Setting up data directories..."
New-Item -ItemType Directory -Path $VectorDbDir -Force | Out-Null

# Check for .env file and create from example if it doesn't exist
$EnvExampleFilePath = Join-Path -Path $BackendDir -ChildPath ".env.example"
if (-not (Test-Path $EnvFilePath) -and (Test-Path $EnvExampleFilePath)) {
    Write-Host "Creating .env file from example..."
    Copy-Item -Path $EnvExampleFilePath -Destination $EnvFilePath
    Write-Warning "A default .env file has been created. Please edit it with your actual configuration."
}

# Start the FastAPI server
Write-Host "Starting FastAPI server..."
# Use the determined Python executable
& $PythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

Write-Host "Server stopped."

# Return to original directory
Pop-Location