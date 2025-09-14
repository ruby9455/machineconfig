#!/usr/bin/bash
# 🛠️ Development Tools Installation Script

# 🐍 Activate Python virtual environment
. $HOME/code/machineconfig/.venv/bin/activate

# ⚙️ Install development applications
python -m fire machineconfig.scripts.python.devops_devapps_install main --which=AllEssentials  # Installs all essential tools

# 🔄 Reload shell configuration
. $HOME/.bashrc

# 🚫 Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
  deactivate || true
fi

