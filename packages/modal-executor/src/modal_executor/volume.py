"""Volume management for persistent state."""

import modal

# Volume name for shared state
VOLUME_NAME = "harvest-agent-state"

# Standard mount point
MOUNT_PATH = "/mnt/state"

# Volume structure
VOLUME_DIRS = [
    ".cache",  # pip cache, downloaded models
    "git-repos",  # Cloned repository copies
    "checkpoints",  # Agent execution snapshots
    "workspace",  # Shared workspace
]


def get_state_volume() -> modal.Volume:
    """Get or create the shared state volume.

    Returns:
        Modal Volume for persistent state storage
    """
    return modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def get_volume_config() -> dict[str, modal.Volume]:
    """Get volume configuration for Sandbox mounting.

    Returns:
        Dict mapping mount path to Volume
    """
    return {MOUNT_PATH: get_state_volume()}


async def initialize_volume_structure(sb: modal.Sandbox) -> None:
    """Initialize standard directory structure in volume.

    Args:
        sb: Active Sandbox with volume mounted
    """
    for dir_name in VOLUME_DIRS:
        dir_path = f"{MOUNT_PATH}/{dir_name}"
        sb.exec("mkdir", "-p", dir_path)


async def cleanup_stale_files(
    sb: modal.Sandbox,
    max_age_days: int = 7,
) -> int:
    """Clean up files older than max_age_days.

    Args:
        sb: Active Sandbox with volume mounted
        max_age_days: Maximum file age in days

    Returns:
        Number of files cleaned up
    """
    # Find and delete old files in cache
    result = sb.exec(
        "find",
        f"{MOUNT_PATH}/.cache",
        "-type",
        "f",
        "-mtime",
        f"+{max_age_days}",
        "-delete",
        "-print",
    )

    # Count deleted files
    stdout = result.stdout.read()
    deleted = stdout.strip().split("\n") if stdout.strip() else []
    return len(deleted)
