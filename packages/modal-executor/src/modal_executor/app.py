"""Modal App definition for Harvest Agent Executor."""

import modal

# Initialize Modal app
app = modal.App("harvest-agent-executor")

# App configuration will be extended by:
# - images.py: Base image definitions
# - scheduler.py: Cron job for environment refresh
# - sandbox.py: Sandbox execution logic
