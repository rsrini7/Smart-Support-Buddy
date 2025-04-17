#!/usr/bin/env python3

"""
Support Buddy - Backend Runner Script

This script provides a convenient way to set up and run the FastAPI backend
for the Support Buddy application. It handles:
- Virtual environment setup
- Dependency installation
- Environment configuration
- Directory creation
- Server startup with configurable options
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if not (sys.version_info.major == 3 and sys.version_info.minor in (10, 11)):
        print("Error: This project requires Python 3.10 or 3.11. You are using Python {}.{}".format(sys.version_info.major, sys.version_info.minor))
        sys.exit(1)


def setup_virtual_env(venv_path):
    """Set up virtual environment if it doesn't exist using uv"""
    if not os.path.exists(venv_path):
        print("Creating virtual environment with uv...")
        subprocess.run(["uv", "venv", venv_path], check=True)
        print(f"Virtual environment created at {venv_path}")
    else:
        print(f"Using existing virtual environment at {venv_path}")


def get_venv_python(venv_path):
    """Get the path to the Python executable in the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_path, 'Scripts', 'python.exe')
    else:  # Unix-like
        return os.path.join(venv_path, 'bin', 'python')


def get_venv_pip(venv_path):
    """Get the path to the pip executable in the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_path, 'Scripts', 'pip.exe')
    else:  # Unix-like
        return os.path.join(venv_path, 'bin', 'pip')


def install_dependencies(venv_path, requirements_path):
    """Install dependencies from requirements.txt using uv"""
    print("Installing dependencies with uv...")
    # Get the path to the Python executable in the virtual environment
    if os.name == 'nt':  # Windows
        python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:  # Unix-like
        python_path = os.path.join(venv_path, 'bin', 'python')
    # Use uv pip install with the --python flag to specify the virtual environment
    subprocess.run(["uv", "pip", "install", "-r", requirements_path, "--python", python_path], check=True)
    print("Dependencies installed successfully")


def setup_env_file(backend_dir):
    """Set up .env file from example if it doesn't exist"""
    env_file = os.path.join(backend_dir, ".env")
    env_example = os.path.join(backend_dir, ".env.example")
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        print("Creating .env file from example...")
        shutil.copy(env_example, env_file)
        print("WARNING: A default .env file has been created. Please edit it with your actual configuration.")
    elif not os.path.exists(env_file) and not os.path.exists(env_example):
        print("WARNING: No .env file or .env.example found. You may need to create one manually.")
    else:
        print("Using existing .env configuration")


def create_data_directories(backend_dir):
    """Create necessary data directories"""
    data_dir = os.path.join(backend_dir, "data")
    vector_db_dir = os.path.join(data_dir, "vectordb")
    
    os.makedirs(vector_db_dir, exist_ok=True)
    print(f"Data directories created at {data_dir}")


def start_server(venv_python, backend_dir, host, port, reload):
    """Start the FastAPI server"""
    os.chdir(backend_dir)
    reload_flag = "--reload" if reload else ""
    
    print(f"Starting FastAPI server on {host}:{port}...")
    cmd = [venv_python, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Support Buddy Backend Runner")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on code changes")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--venv", default="venv", help="Path to virtual environment (default: venv)")
    args = parser.parse_args()
    
    # Get project directories
    project_root = Path(__file__).parent.absolute()
    backend_dir = os.path.join(project_root, "backend")
    requirements_path = os.path.join(project_root, "requirements.txt")
    venv_path = os.path.join(project_root, args.venv)
    
    # Check Python version
    check_python_version()
    
    # Setup virtual environment
    setup_virtual_env(venv_path)
    venv_python = get_venv_python(venv_path)
    venv_pip = get_venv_pip(venv_path)
    
    # Install dependencies if not skipped
    if not args.skip_deps:
        install_dependencies(venv_path, requirements_path)
    
    # Setup environment and directories
    setup_env_file(backend_dir)
    create_data_directories(backend_dir)
    
    # Start the server
    start_server(venv_python, backend_dir, args.host, args.port, not args.no_reload)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)