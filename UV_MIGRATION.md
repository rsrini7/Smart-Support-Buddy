# Migration from venv to uv

This project has been migrated from using the standard `venv` module to `uv` for virtual environment management and package installation. This document explains the changes made and how to use the new system.

## What is uv?

`uv` is a fast Python package installer and resolver written in Rust. It's designed to be a drop-in replacement for pip and virtualenv with significantly improved performance. Key benefits include:

- Much faster dependency resolution and installation
- Improved caching for faster repeated installations
- Compatible with existing requirements.txt files
- Simplified virtual environment management

## Changes Made

The following files have been updated to use `uv` instead of `venv`/`pip`:

1. `start_backend.sh` - Now uses `uv venv` to create virtual environments and `uv pip install` to install dependencies
2. `run_backend.py` - Updated to use `uv` commands for environment creation and package installation

## Using the Updated Scripts

### Prerequisites

You need to have `uv` installed on your system. If you don't have it installed, you can install it using:

```bash
# Using pip
pip install uv

# Using Homebrew (macOS)
brew install uv

# Using cargo (Rust package manager)
cargo install uv
```

### Running the Backend

The commands to run the backend remain the same:

```bash
# Using the shell script
./start_backend.sh

# Using the Python script
python run_backend.py
```

### Manual Virtual Environment Management

If you need to manually manage the virtual environment:

```bash
# Create a new virtual environment
uv venv venv

# Activate the virtual environment
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate    # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

## Troubleshooting

### Common Issues

1. **uv command not found**: Ensure that `uv` is installed and in your PATH
2. **Permission issues**: You may need to use `sudo` or run as administrator when installing `uv` globally
3. **Compatibility issues**: If you encounter any package compatibility issues, try using the `--legacy-resolver` flag with `uv pip install`

### Reverting to venv

If you need to revert to using the standard `venv` module:

1. Delete the existing virtual environment: `rm -rf venv`
2. Create a new one with venv: `python -m venv venv`
3. Install dependencies with pip: `pip install -r requirements.txt`

## Additional Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv vs pip Comparison](https://astral.sh/blog/uv)