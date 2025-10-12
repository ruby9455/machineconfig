
import typer
from typing import Optional, Literal
from pathlib import Path


def main(
    cloud: Optional[str] = typer.Option(None, "--cloud", "-c", help="Cloud storage profile name. If not provided, uses default from config."),
    repo: Optional[str] = typer.Option(Path.cwd().as_posix(), "--repo", "-r", help="Path to the local repository. Defaults to cwd."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message for local changes."),
    on_conflict: Literal["ask", "push-local-merge", "overwrite-local", "stop-on-conflict", "remove-rclone-conflict"] = typer.Option("ask", "--on-conflict", "-oc", help="Action to take on merge conflict. Default is 'ask'."),
    pwd: Optional[str] = typer.Option(None, "--password", help="Password for encryption/decryption of the remote repository."),
):
    from machineconfig.scripts.python.helpers_repos.cloud_repo_sync import main as program_content
    program_content(cloud=cloud, repo=repo, message=message, on_conflict=on_conflict, pwd=pwd)
