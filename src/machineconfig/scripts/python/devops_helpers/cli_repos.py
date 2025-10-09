"""Repos CLI powered by Typer.

# TODO use gh api user --jq '.login' to get the username and use it to clone the repos.
in the event that username@github.com is not mentioned in the remote url.

"""

from pathlib import Path
from typing import Annotated, Optional
import typer
from machineconfig.scripts.python.helpers_repos.secure_repo import main as secure_repo_main


DirectoryArgument = Annotated[Optional[str], typer.Argument(help="📁 Directory containing repo(s).")]
RecursiveOption = Annotated[bool, typer.Option("--recursive", "-r", help="🔍 Recurse into nested repositories.")]
NoSyncOption = Annotated[bool, typer.Option("--no-sync", help="🚫 Disable automatic uv sync after pulls.")]
CloudOption = Annotated[Optional[str], typer.Option("--cloud", "-c", help="☁️ Upload to or download from this cloud remote.")]


def push(directory: DirectoryArgument = None, recursive: RecursiveOption = False, no_sync: NoSyncOption = False) -> None:
    """🚀 Push changes across repositories."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import git_operations
    git_operations(directory, pull=False, commit=False, push=True, recursive=recursive, no_sync=no_sync)


def pull(directory: DirectoryArgument = None, recursive: RecursiveOption = False, no_sync: NoSyncOption = False) -> None:
    """⬇️ Pull changes across repositories."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import git_operations

    git_operations(directory, pull=True, commit=False, push=False, recursive=recursive, no_sync=no_sync)


def commit(directory: DirectoryArgument = None, recursive: RecursiveOption = False, no_sync: NoSyncOption = False) -> None:
    """💾 Commit changes across repositories."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import git_operations

    git_operations(directory, pull=False, commit=True, push=False, recursive=recursive, no_sync=no_sync)


def sync(directory: DirectoryArgument = None, recursive: RecursiveOption = False, no_sync: NoSyncOption = False) -> None:
    """🔄 Pull, commit, and push changes across repositories."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import git_operations
    git_operations(directory, pull=True, commit=True, push=True, recursive=recursive, no_sync=no_sync)


def capture(directory: DirectoryArgument = None, cloud: CloudOption = None) -> None:
    """📝 Record repositories into a repos.json specification."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import resolve_directory
    repos_root = resolve_directory(directory)
    from machineconfig.scripts.python.repos_helpers.record import main as record_repos

    save_path = record_repos(repos_root=repos_root)
    from machineconfig.utils.path_extended import PathExtended

    if cloud is not None:
        PathExtended(save_path).to_cloud(rel2home=True, cloud=cloud)


def clone(directory: DirectoryArgument = None, cloud: CloudOption = None) -> None:
    """📥 Clone repositories described by a repos.json specification."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import clone_from_specs

    
    clone_from_specs(directory, cloud, checkout_branch_flag=False, checkout_commit_flag=False)


def checkout_command(directory: DirectoryArgument = None, cloud: CloudOption = None) -> None:
    """🔀 Check out specific commits listed in the specification."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import clone_from_specs

    
    clone_from_specs(directory, cloud, checkout_branch_flag=False, checkout_commit_flag=True)


def checkout_to_branch_command(directory: DirectoryArgument = None, cloud: CloudOption = None) -> None:
    """🔀 Check out to the main branch defined in the specification."""
    from machineconfig.scripts.python.repos_helpers.entrypoint import clone_from_specs
    clone_from_specs(directory, cloud, checkout_branch_flag=True, checkout_commit_flag=False)


def analyze(directory: DirectoryArgument = None) -> None:
    """📊 Analyze repository development over time."""
    repo_path = directory if directory is not None else "."
    from machineconfig.scripts.python.repos_helpers.count_lines_frontend import analyze_repo_development

    analyze_repo_development(repo_path=repo_path)


def viz(
    repo: str = typer.Option(Path.cwd().__str__(), "--repo", "-r", help="Path to git repository to visualize"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output video file (e.g., output.mp4). If specified, gource will render to video."),
    resolution: str = typer.Option("1920x1080", "--resolution", "-res", help="Video resolution (e.g., 1920x1080, 1280x720)"),
    seconds_per_day: float = typer.Option(0.1, "--seconds-per-day", "-spd", help="Speed of simulation (lower = faster)"),
    auto_skip_seconds: float = typer.Option(1.0, "--auto-skip-seconds", "-as", help="Skip to next entry if nothing happens for X seconds"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title for the visualization"),
    hide_items: list[str] = typer.Option([], "--hide", "-h", help="Items to hide: bloom, date, dirnames, files, filenames, mouse, progress, root, tree, users, usernames"),
    key_items: bool = typer.Option(False, "--key", "-k", help="Show file extension key"),
    fullscreen: bool = typer.Option(False, "--fullscreen", "-f", help="Run in fullscreen mode"),
    viewport: Optional[str] = typer.Option(None, "--viewport", "-v", help="Camera viewport (e.g., '1000x1000')"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    stop_date: Optional[str] = typer.Option(None, "--stop-date", help="Stop date (YYYY-MM-DD)"),
    user_image_dir: Optional[Path] = typer.Option(None, "--user-image-dir", help="Directory with user avatar images"),
    max_files: int = typer.Option(0, "--max-files", help="Maximum number of files to show (0 = no limit)"),
    max_file_lag: float = typer.Option(5.0, "--max-file-lag", help="Max time files remain on screen after last change"),
    file_idle_time: int = typer.Option(0, "--file-idle-time", help="Time in seconds files remain idle before being removed"),
    framerate: int = typer.Option(60, "--framerate", help="Frames per second for video output"),
    background_color: str = typer.Option("000000", "--background-color", help="Background color in hex (e.g., 000000 for black)"),
    font_size: int = typer.Option(22, "--font-size", help="Font size"),
    camera_mode: str = typer.Option("overview", "--camera-mode", help="Camera mode: overview or track"),
        ) -> None:
    """🎬 Visualize repository activity using Gource."""
    from machineconfig.scripts.python.helpers_repos.grource import visualize
    visualize(repo=repo, output_file=output_file, resolution=resolution, seconds_per_day=seconds_per_day,
              auto_skip_seconds=auto_skip_seconds, title=title, hide_items=hide_items, key_items=key_items,
              fullscreen=fullscreen, viewport=viewport, start_date=start_date, stop_date=stop_date,
              user_image_dir=user_image_dir, max_files=max_files, max_file_lag=max_file_lag,
              file_idle_time=file_idle_time, framerate=framerate, background_color=background_color,
              font_size=font_size, camera_mode=camera_mode)


def cleanup(repo: DirectoryArgument = None, recursive: RecursiveOption = False) -> None:
    """🧹 Clean repository directories from cache files."""
    if repo is None:
        repo = Path.cwd().as_posix()
    
    arg_path = Path(repo).expanduser().absolute()
    from git import Repo, InvalidGitRepositoryError
    if not recursive:
        # Check if the directory is a git repo
        try:
            Repo(str(arg_path), search_parent_directories=False)
        except InvalidGitRepositoryError:
            typer.echo(f"❌ {arg_path} is not a git repository. Use -r flag for recursive cleanup.")
            return
        # Run cleanup on this repo
        repos_to_clean = [arg_path]
    else:
        # Find all git repos recursively under the directory
        git_dirs = list(arg_path.rglob('.git'))
        repos_to_clean = [git_dir.parent for git_dir in git_dirs if git_dir.is_dir()]
        if not repos_to_clean:
            typer.echo(f"❌ No git repositories found under {arg_path}")
            return
    
    for repo_path in repos_to_clean:
        typer.echo(f"🧹 Cleaning {repo_path}")
        script = fr"""
cd "{repo_path}"
uv run --with cleanpy cleanpy .
# mcinit .
# find "." -type f \( -name "*.py" -o -name "*.md" -o -name "*.json" \) -not -path "*/\.*" -not -path "*/__pycache__/*" -print0 | xargs -0 sed -i 's/[[:space:]]*$//'
"""
        from machineconfig.utils.code import run_shell_script
        run_shell_script(script)


def get_app():
    repos_apps = typer.Typer(help="📁 [r] Manage development repositories", no_args_is_help=True)
    mirror_app = typer.Typer(help="🔄 [m] Manage repository specifications and syncing", no_args_is_help=True)
    repos_apps.add_typer(mirror_app, name="mirror", help="🔄  [m] mirror repositories using saved specs")
    repos_apps.add_typer(mirror_app, name="m", help="mirror repositories using saved specs", hidden=True)

    repos_apps.command(name="push", help="🚀  [p] Push changes across repositories")(push)
    repos_apps.command(name="p", help="Push changes across repositories", hidden=True)(push)
    repos_apps.command(name="pull", help="⬇️   [P] Pull changes across repositories")(pull)
    repos_apps.command(name="P", help="Pull changes across repositories", hidden=True)(pull)
    repos_apps.command(name="commit", help="💾  [c] Commit changes across repositories")(commit)
    repos_apps.command(name="c", help="Commit changes across repositories", hidden=True)(commit)
    repos_apps.command(name="sync", help="🔄  [s] Pull, commit, and push changes across repositories")(sync)
    repos_apps.command(name="s", help="Pull, commit, and push changes across repositories", hidden=True)(sync)
    repos_apps.command(name="analyze", help="📊  [a] Analyze repository development over time")(analyze)
    repos_apps.command(name="a", help="Analyze repository development over time", hidden=True)(analyze)
    repos_apps.command(name="secure", help="🔐  [s] Securely sync git repository to/from cloud with encryption")(secure_repo_main)
    repos_apps.command(name="s", help="Securely sync git repository to/from cloud with encryption", hidden=True)(secure_repo_main)
    repos_apps.command(name="viz", help="🎬  [v] Visualize repository activity using Gource")(viz)
    repos_apps.command(name="v", help="Visualize repository activity using Gource", hidden=True)(viz)
    repos_apps.command(name="cleanup", help="🧹  [n] Clean repository directories from cache files")(cleanup)
    repos_apps.command(name="n", help="Clean repository directories from cache files", hidden=True)(cleanup)

    mirror_app.command(name="capture", help="📝  [cap] Record repositories into a repos.json specification")(capture)
    mirror_app.command(name="cap", help="Record repositories into a repos.json specification", hidden=True)(capture)
    mirror_app.command(name="clone", help="📥  [clo] Clone repositories described by a repos.json specification")(clone)
    mirror_app.command(name="clo", help="Clone repositories described by a repos.json specification", hidden=True)(clone)
    mirror_app.command(name="checkout-to-commit", help="🔀  [ctc] Check out specific commits listed in the specification")(checkout_command)
    mirror_app.command(name="ctc", help="Check out specific commits listed in the specification", hidden=True)(checkout_command)
    mirror_app.command(name="checkout-to-branch", help="🔀  [ctb] Check out to the main branch defined in the specification")(checkout_to_branch_command)
    mirror_app.command(name="ctb", help="Check out to the main branch defined in the specification", hidden=True)(checkout_to_branch_command)

    return repos_apps
