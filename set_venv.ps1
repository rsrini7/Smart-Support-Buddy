# This script activates the Python virtual environment for the backend in PowerShell
# Must be dot-sourced: . .\set_venv.ps1

# Get the directory of the current script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Construct the path to the PowerShell activation script
$VenvActivateScript = Join-Path -Path $ScriptDir -ChildPath "backend\.venv\Scripts\Activate.ps1"

# Check if the activation script exists
if (Test-Path $VenvActivateScript) {
    Write-Host "Activating backend virtual environment..."
    . $VenvActivateScript
} else {
    Write-Error "Virtual environment activation script not found at $VenvActivateScript"
    # Use exit 1 for scripts, but since this should be sourced, we might just let the error propagate
    # or use 'return' if inside a function, but here 'exit' might stop the parent script if not sourced.
    # A warning might be better if sourcing is expected.
    Write-Warning "Ensure the backend virtual environment has been created correctly."
    # Consider returning a specific status or object if used programmatically
}