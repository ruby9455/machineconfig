"""devops with emojis"""

import machineconfig.utils.installer_utils.installer as installer_entry_point
import machineconfig.scripts.python.share_terminal as share_terminal
import machineconfig.scripts.python.repos as repos

import machineconfig.profile.create_frontend as create_frontend
# import machineconfig.scripts.python.dotfile as dotfile_module
import typer
from typing import Literal, Annotated


app = typer.Typer(help="🛠️ DevOps operations", no_args_is_help=True)
app.command(name="install", help="📦 Install essential packages")(installer_entry_point.main)
app.add_typer(repos.app, name="repos", help="📁 Manage git repositories")


config_apps = typer.Typer(help="⚙️ Configuration subcommands", no_args_is_help=True)
app.add_typer(config_apps, name="config")



app_data = typer.Typer(help="💾 Data subcommands", no_args_is_help=True)
app.add_typer(app_data, name="data")

nw_apps = typer.Typer(help="🔐 Network subcommands", no_args_is_help=True)
nw_apps.command(name="share-terminal", help="📡 Share terminal via web browser")(share_terminal.main)
app.add_typer(nw_apps, name="network")


self_app = typer.Typer(help="🔄 SELF operations subcommands", no_args_is_help=True)
app.add_typer(self_app, name="self")


@self_app.command()
def update():
    """🔄 UPDATE essential repos"""
    import machineconfig.scripts.python.devops_update_repos as helper
    helper.main()
@self_app.command()
def interactive():
    """🤖 INTERACTIVE configuration of machine."""
    from machineconfig.scripts.python.interactive import main
    main()
@self_app.command()
def status():
    """📊 STATUS of machine, shell profile, apps, symlinks, dotfiles, etc."""
    pass


@config_apps.command(no_args_is_help=True)
def private():
    """🔗 Manage private configuration files."""
    create_frontend.main_private_from_parser()

@config_apps.command(no_args_is_help=True)
def public():
    """🔗 Manage public configuration files."""
    create_frontend.main_public_from_parser()

# @config_apps.command(no_args_is_help=True)
# def dotfile():
#     """🔗 Manage dotfiles."""
#     dotfile_module.main()


@config_apps.command(no_args_is_help=True)
def shell(method: Annotated[Literal["copy", "reference"], typer.Argument(help="Choose the method to configure the shell profile: 'copy' copies the init script directly, 'reference' references machineconfig for dynamic updates.")]):
    """🔗 Configure your shell profile."""
    from machineconfig.profile.shell import create_default_shell_profile
    create_default_shell_profile(method=method)


@nw_apps.command()
def add_key():
    """🔑 SSH add pub key to this machine"""
    import machineconfig.scripts.python.devops_add_ssh_key as helper
    helper.main()
@nw_apps.command()
def add_identity():
    """🗝️ SSH add identity (private key) to this machine"""
    import machineconfig.scripts.python.devops_add_identity as helper
    helper.main()
@nw_apps.command()
def connect():
    """🔐 SSH use key pair to connect two machines"""
    raise NotImplementedError

@nw_apps.command()
def setup():
    """📡 SSH setup"""
    import platform
    if platform.system() == "Windows":
        from machineconfig.setup_windows import SSH_SERVER
        program = SSH_SERVER.read_text(encoding="utf-8")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        from machineconfig.setup_linux import SSH_SERVER
        program = SSH_SERVER.read_text(encoding="utf-8")
    else:
        raise NotImplementedError(f"Platform {platform.system()} is not supported.")
    from machineconfig.utils.code import run_shell_script
    run_shell_script(program=program)


@app_data.command()
def backup():
    """💾 BACKUP"""
    from machineconfig.scripts.python.devops_backup_retrieve import main_backup_retrieve
    main_backup_retrieve(direction="BACKUP")


@app_data.command()
def retrieve():
    """📥 RETRIEVE"""
    from machineconfig.scripts.python.devops_backup_retrieve import main_backup_retrieve
    main_backup_retrieve(direction="RETRIEVE")


# @app.command()
# def scheduler():
#     """⏰ SCHEDULER"""
#     # from machineconfig.scripts.python.scheduler import main as helper
#     # helper()



# @app.command()
# def scheduler():
#     """⏰ SCHEDULER"""
#     # from machineconfig.scripts.python.scheduler import main as helper
#     # helper()


if __name__ == "__main__":
    pass
