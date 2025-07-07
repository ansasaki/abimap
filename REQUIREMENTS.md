# Requirements Files

This document explains the different requirements files available for the abimap project and how to use them.

## Overview

The abimap project uses multiple requirements files to organize dependencies for different use cases:

## Requirements Files

### Core Requirements

- **`requirements.txt`** - Runtime dependencies for production use
  ```bash
  pip install -r requirements.txt
  ```

- **`requirements-minimal.txt`** - Absolute minimum requirements
  ```bash
  pip install -r requirements-minimal.txt
  ```

### Development Requirements

- **`requirements-dev.txt`** - Complete development environment
  ```bash
  pip install -r requirements-dev.txt
  ```
  Includes testing, documentation, code quality, and build tools.

- **`requirements-test.txt`** - Testing dependencies only
  ```bash
  pip install -r requirements-test.txt
  ```

### Documentation Requirements

- **`docs/requirements.txt`** - Documentation building dependencies
  ```bash
  pip install -r docs/requirements.txt
  ```

### CI/CD Requirements

- **`requirements-ci.txt`** - CI/CD environment dependencies
  ```bash
  pip install -r requirements-ci.txt
  ```

## Usage Examples

### For End Users
```bash
# Install abimap for normal use
pip install abimap
# or
pip install -r requirements.txt
```

### For Contributors
```bash
# Set up complete development environment
pip install -r requirements-dev.txt

# Or install specific components
pip install -r requirements-test.txt    # For testing only
pip install -r docs/requirements.txt    # For documentation only
```

### For CI/CD
```bash
# In GitHub Actions or other CI systems
pip install -r requirements-ci.txt
```

## Dependency Management

The requirements files are organized hierarchically:
- `requirements-dev.txt` includes `requirements-test.txt` and `docs/requirements.txt`
- `requirements-ci.txt` includes `requirements-test.txt`
- All files include `-e .` for development installation

## Version Constraints

All requirements files use minimum version constraints (e.g., `>=6.0.0`) to ensure:
- Compatibility with the latest Python versions
- Security updates are automatically included
- Forward compatibility with newer package versions

## Updating Requirements

To update requirements:
1. Edit the appropriate requirements file
2. Test the changes in a clean environment
3. Update version constraints as needed
4. Run tests to ensure compatibility

## Python Version Support

All requirements are compatible with Python 3.9+ as specified in `pyproject.toml`. 