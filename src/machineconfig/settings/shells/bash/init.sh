#!/bin/bash
# 🛠️ Bash Shell Configuration and Initialization

add_to_path_if_not_already() {
    for dir in "$@"; do
        if [[ ! $PATH =~ (^|:)"${dir}"(:|$) ]]; then
            export PATH="$PATH:${dir}"
        fi
    done
}
CONFIG_ROOT="$HOME/.config/machineconfig"

# 📂 Add directories to PATH
add_to_path_if_not_already \
    "$HOME/.local/bin" \
    "$HOME/.cargo/bin" \
    "$CONFIG_ROOT/scripts/linux" \
    "$HOME/dotfiles/scripts/linux" \
    "$HOME/.nix-profile/bin" \
    "/home/linuxbrew/.linuxbrew/bin" \
    "/usr/games"
# this way, if the script was run multiple times, e.g. due to nested shells in zellij, there will be no duplicates in the path
# export DISPLAY=localhost:0.0  # xming server


# echo "Sourcing scripts ..."
. $CONFIG_ROOT/settings/broot/br.sh
. $CONFIG_ROOT/settings/lf/linux/exe/lfcd.sh
. $CONFIG_ROOT/settings/tere/terecd.sh

if [ -d $CONFIG_ROOT ]; then
    source $CONFIG_ROOT/settings/shells/bash/commands.sh
fi

# set alias l to lsd -la
alias l='lsd -la'
alias gcs='gh copilot suggest -t shell'
alias gcg='gh copilot suggest -t git'
alias gce='gh copilot explain'
# Check uniqueness of aliases
# type gcs
# type gcg
# type gce

gcd() {
  x=$(history -p '!!')
  y=$(eval "$x" 2>&1)
  gh copilot explain "Input command is: $x The output is this: $y"
}

# 📦 Node Version Manager
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
# [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion


# source /home/alex/.config/broot/launcher/bash/br
# eval "$(thefuck --alias)"
# from https://github.com/ajeetdsouza/zoxide
eval "$(zoxide init bash)"
# from https://github.com/starship/starship
eval "$(starship init bash)"
# https://github.com/atuinsh/atuin
# eval "$(atuin init bash)"
# LEVE THIS IN THE END TO AVOID EXECUTION FAILURE OF THE REST OF THE SCRIPT
# from https://github.com/cantino/mcfly
eval "$(mcfly init bash)"

# check if file in ~/dotfiles/machineconfig/init_linux.sh exists and source it
if [ -f "$HOME/dotfiles/machineconfig/init_linux.sh" ]; then
    # echo "Sourcing $HOME/dotfiles/machineconfig/init_linux.sh"
    source "$HOME/dotfiles/machineconfig/init_linux.sh"
fi
