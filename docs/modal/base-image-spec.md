# Base Image Specification

The Modal Executor uses a custom base image for Sandbox execution.

## Image Configuration

**Base**: Debian Slim with Python 3.11
**Target Size**: <800MB
**Location**: `packages/modal-executor/src/modal_executor/images.py`

## Installed Packages

### System Packages (apt)

| Package | Purpose |
|---------|---------|
| `git` | Version control |
| `curl` | HTTP requests |
| `wget` | File downloads |
| `build-essential` | C/C++ compilation for native extensions |
| `libffi-dev` | Foreign function interface |
| `libssl-dev` | SSL/TLS support |
| `zlib1g-dev` | Compression libraries |
| `jq` | JSON processing |

### Python Packages (pip)

| Package | Purpose |
|---------|---------|
| `uv` | Fast package installer |
| `requests` | HTTP library |
| `httpx` | Async HTTP |
| `pydantic>=2.0` | Data validation |
| `python-dotenv` | Environment file loading |
| `pyyaml` | YAML parsing |

## Directory Structure

Created during image build:

```
/workspace/           # Working directory for code execution
/mnt/state/.cache/    # pip cache, downloaded models
/mnt/state/git-repos/ # Cloned repository copies
/mnt/state/checkpoints/ # Agent execution snapshots
```

## Extending the Image

### Adding Pip Packages

```python
from modal_executor.images import get_base_image_with_extras

# Create extended image
image = get_base_image_with_extras(["pandas", "numpy", "scikit-learn"])
```

### Custom Image

```python
import modal
from modal_executor.images import get_base_image

# Extend base with additional setup
custom_image = (
    get_base_image()
    .pip_install("your-package")
    .run_commands("custom setup command")
)
```

## Layer Optimization

Image layers are ordered for optimal caching:

1. **Base OS** (debian_slim) - Rarely changes
2. **System packages** (apt_install) - Rarely changes
3. **Python packages** (pip_install) - Occasional updates
4. **Directory setup** (run_commands) - Rarely changes

Put frequently-changing content in separate images or at runtime.

## Force Rebuild

To rebuild the image (e.g., after dependency updates):

```bash
MODAL_FORCE_BUILD=1 modal run ...
```

Or programmatically:

```python
image = modal.Image.debian_slim(..., force_build=True)
```

## Size Monitoring

Check image size in Modal dashboard or via:

```python
# In a Sandbox
sb.exec("du", "-sh", "/")
```

Target: <800MB total

## Scheduled Refresh

The base image is warmed up every 30 minutes via cron job:
- Ensures fast cold starts
- Validates image is working
- Cleans up stale cache files

See `scheduler.py` for implementation.
