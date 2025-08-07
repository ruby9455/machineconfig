"""BR: Backup and Retrieve
"""

# import subprocess
from crocodile.file_management import Read, P
from machineconfig.utils.utils import LIBRARY_ROOT, DEFAULTS_PATH, print_code, choose_cloud_interactively, choose_multiple_options
from machineconfig.scripts.python.helpers.helpers2 import ES
from platform import system
from typing import Any, Literal, Optional
from rich.console import Console
from rich.panel import Panel


OPTIONS = Literal["BACKUP", "RETRIEVE"]


def main_backup_retrieve(direction: OPTIONS, which: Optional[str] = None):
    console = Console()
    
    try:
        cloud: str = Read.ini(DEFAULTS_PATH)['general']['rclone_config_name']
        console.print(Panel(f"⚠️  DEFAULT CLOUD CONFIGURATION\n🌥️  Using default cloud: {cloud}", title="[bold blue]Cloud Configuration[/bold blue]", border_style="blue"))
    except (FileNotFoundError, KeyError, IndexError):
        console.print(Panel("🔍 DEFAULT CLOUD NOT FOUND\n🔄 Please select a cloud configuration from the options below", title="[bold red]Error: Cloud Not Found[/bold red]", border_style="red"))
        cloud = choose_cloud_interactively()

    bu_file: dict[str, Any] = Read.toml(LIBRARY_ROOT.joinpath("profile/backup.toml"))
    
    console.print(Panel(f"🧰 LOADING BACKUP CONFIGURATION\n📄 File: {LIBRARY_ROOT.joinpath('profile/backup.toml')}", title="[bold blue]Backup Configuration[/bold blue]", border_style="blue"))
    
    if system() == "Linux": 
        bu_file = {key: val for key, val in bu_file.items() if "windows" not in key}
        console.print(Panel(f"🐧 LINUX ENVIRONMENT DETECTED\n🔍 Filtering out Windows-specific entries\n✅ Found {len(bu_file)} applicable backup configuration entries", title="[bold blue]Linux Environment[/bold blue]", border_style="blue"))
    elif system() == "Windows": 
        bu_file = {key: val for key, val in bu_file.items() if "linux" not in key}
        console.print(Panel(f"🪟 WINDOWS ENVIRONMENT DETECTED\n🔍 Filtering out Linux-specific entries\n✅ Found {len(bu_file)} applicable backup configuration entries", title="[bold blue]Windows Environment[/bold blue]", border_style="blue"))

    if which is None:
        console.print(Panel(f"🔍 SELECT {direction} ITEMS\n📋 Choose which configuration entries to process", title="[bold blue]Select Items[/bold blue]", border_style="blue"))
        choices = choose_multiple_options(msg=f"WHICH FILE of the following do you want to {direction}?", options=['all'] + list(bu_file.keys()))
    else:
        choices = which.split(",") if which else []
        console.print(Panel(f"🔖 PRE-SELECTED ITEMS\n📝 Using: {', '.join(choices)}", title="[bold blue]Pre-selected Items[/bold blue]", border_style="blue"))

    if "all" in choices:
        items = bu_file
        console.print(Panel(f"📋 PROCESSING ALL ENTRIES\n🔢 Total entries to process: {len(bu_file)}", title="[bold blue]Process All Entries[/bold blue]", border_style="blue"))
    else:
        items = {key: val for key, val in bu_file.items() if key in choices}
        console.print(Panel(f"📋 PROCESSING SELECTED ENTRIES\n🔢 Total entries to process: {len(items)}", title="[bold blue]Process Selected Entries[/bold blue]", border_style="blue"))
    program = f"""$cloud = "{cloud}:{ES}" \n """ if system() == "Windows" else f"""cloud="{cloud}:{ES}" \n """
    console.print(Panel(f"🚀 GENERATING {direction} SCRIPT\n🌥️  Cloud: {cloud}\n🗂️  Items: {len(items)}", title="[bold blue]Script Generation[/bold blue]", border_style="blue"))
    for item_name, item in items.items():
        flags = ''
        flags += 'z' if item['zip'] == 'True' else ''
        flags += 'e' if item['encrypt'] == 'True' else ''
        flags += 'r' if item['rel2home'] == 'True' else ''
        flags += 'o' if system().lower() in item_name else ''
        console.print(Panel(f"📦 PROCESSING: {item_name}\n📂 Path: {P(item['path']).as_posix()}\n🏳️  Flags: {flags or 'None'}", title=f"[bold blue]Processing Item: {item_name}[/bold blue]", border_style="blue"))
        if flags: flags = "-" + flags
        if direction == "BACKUP": 
            program += f"""\ncloud_copy "{P(item['path']).as_posix()}" $cloud {flags}\n"""
        elif direction == "RETRIEVE": 
            program += f"""\ncloud_copy $cloud "{P(item['path']).as_posix()}" {flags}\n"""
        else:
            console.print(Panel("❌ ERROR: INVALID DIRECTION\n⚠️  Direction must be either \"BACKUP\" or \"RETRIEVE\"", title="[bold red]Error: Invalid Direction[/bold red]", border_style="red"))
            raise RuntimeError(f"Unknown direction: {direction}")            
        if item_name == "dotfiles" and system() == "Linux": 
            program += """\nchmod 700 ~/.ssh/*\n"""
            console.print(Panel("🔒 SPECIAL HANDLING: SSH PERMISSIONS\n🛠️  Setting secure permissions for SSH files\n📝 Command: chmod 700 ~/.ssh/*", title="[bold blue]Special Handling: SSH Permissions[/bold blue]", border_style="blue"))
    print_code(program, lexer="shell", desc=f"{direction} script")
    console.print(Panel(f"✅ {direction} SCRIPT GENERATION COMPLETE\n🚀 Ready to execute the operations", title="[bold green]Script Generation Complete[/bold green]", border_style="green"))
    return program


def main(direction: OPTIONS, which: Optional[str] = None):
    console = Console()
    
    console.print(Panel(f"🔄 {direction} OPERATION STARTED\n⏱️  {'-' * 58}", title="[bold blue]Operation Initiated[/bold blue]", border_style="blue"))
    
    code = main_backup_retrieve(direction=direction, which=which)
    from machineconfig.utils.utils import write_shell_script_to_default_program_path
    
    console.print(Panel("💾 GENERATING SHELL SCRIPT\n📄 Filename: backup_retrieve.sh", title="[bold blue]Shell Script Generation[/bold blue]", border_style="blue"))
    
    write_shell_script_to_default_program_path(program=code, desc="backup_retrieve.sh", preserve_cwd=True, display=True, execute=False)


if __name__ == "__main__":
    pass
