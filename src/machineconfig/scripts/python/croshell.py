#!/usr/bin/env -S uv run --no-dev --project

"""
croshell
"""

from typing import Annotated, Optional
import typer
from machineconfig.utils.path_extended import PathExtended
from machineconfig.utils.accessories import randstr

from machineconfig.utils.options import choose_from_options
# from machineconfig.utils.ve import get_ve_activate_line
from rich.console import Console
from rich.panel import Panel
# from rich.text import Text

console = Console()


def add_print_header_pycode(path: str, title: str):
    return f"""

from machineconfig.utils.path_extended import PathExtended
pycode = PathExtended(r'{path}').read_text(encoding="utf-8")
pycode = pycode.split("except Exception: print(pycode)")[2]

try:
    from rich.text import Text
    from rich.panel import Panel
    from rich.console import Console
    from rich.syntax import Syntax
    console = Console()
    if pycode.strip() != "":
        console.print(Panel(Syntax(pycode, lexer="python"), title='{title}'), style="bold red")
except Exception: print(pycode)
"""


def get_read_data_pycode(path: str):
    return f"""
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
console = Console()
p = PathExtended(r'{path}').absolute()
try:
    from machineconfig.utils.files.read import Read
    from machineconfig.utils.accessories import pprint
    dat = Read.read(p)
    if isinstance(dat, dict):
        panel_title = f"📄 File Data: {{p.name}}"
        console.print(Panel(Text(str(dat), justify="left"), title=panel_title, expand=False))
        pprint(dat, PathExtended.name)
    else:
        panel_title = f"📄 Successfully read the file: {{p.name}}"
        console.print(Panel(Text(str(dat), justify="left"), title=panel_title, expand=False))
except Exception as e:
    error_message = f'''❌ ERROR READING FILE\nFile: {{p.name}}\nError: {{e}}'''
    console.print(Panel(Text(error_message, justify="left"), title="Error", expand=False, border_style="red"))
"""



def main(
    python: Annotated[bool, typer.Option("--python", "-p", help="flag to use python over IPython.")] = False,
    fzf: Annotated[bool, typer.Option("--fzf", "-F", help="search with fuzzy finder for python scripts and run them")] = False,
    profile: Annotated[Optional[str], typer.Option("--profile", "-P", help="ipython profile to use, defaults to default profile.")] = None,
    read: Annotated[str, typer.Option("--read", "-r", help="read a binary file.")] = "",
    jupyter: Annotated[bool, typer.Option("--jupyter", "-j", help="run in jupyter interactive console")] = False,
    streamlit_viewer: Annotated[bool, typer.Option("--stViewer", "-s", help="view in streamlit app")] = False,
    visidata: Annotated[bool, typer.Option("--visidata", "-V", help="open data file in visidata")] = False,
    local: Annotated[bool, typer.Option("--local", "-l", help="run in local mode, not in virtual env.")]= False,
) -> None:
    # ==================================================================================
    # flags processing
    interactivity = "-i"
    interpreter = "python" if python else "ipython"
    ipython_profile: Optional[str] = profile
    file_obj = PathExtended.cwd()  # initialization value, could be modified according to args.

    if fzf:
        text = "🔍 Searching for Python files..."
        console.print(Panel(text, title="[bold blue]Info[/bold blue]"))
        options = [str(item) for item in PathExtended.cwd().search("*.py", r=True)]
        file_selected = choose_from_options(msg="Choose a python file to run", options=options, fzf=True, multi=False)
        assert isinstance(file_selected, str)
        program = PathExtended(file_selected).read_text(encoding="utf-8")
        text = f"📄 Selected file: {PathExtended(file_selected).name}"
        console.print(Panel(text, title="[bold blue]Info[/bold blue]"))

    elif read != "":
        if streamlit_viewer:
            #             text = "📊 STARTING STREAMLIT VIEWER"
            #             console.print(Panel(text, title="[bold blue]Info[/bold blue]"))
            #             from machineconfig.scripts.python.viewer import run
            #             py_file_path = run(data_path=args.read, data=None, get_figure=None)
            #             final_program = f"""
            # #!/bin/bash
            # streamlit run {py_file_path}
            # """
            #             PROGRAM_PATH.write_text(data=final_program, encoding="utf-8")
            return None
        file_obj = PathExtended(str(read).lstrip()).expanduser().absolute()
        program = get_read_data_pycode(str(file_obj))
        text = f"📄 Reading data from: {file_obj.name}"
        console.print(Panel(text, title="[bold blue]Info[/bold blue]"))

    else:  # if nothing is specified, then run in interactive mode.
        text = "⌨️  Entering interactive mode"
        console.print(Panel(text, title="[bold blue]Info[/bold blue]"))
        # from machineconfig.scripts.python.croshell import InteractiveShell
        # InteractiveShell().run()
        # return None
        program = ""

    preprogram = """

#%%

from machineconfig.utils.files.headers import print_header, print_logo
print_header()
print_logo("CROCODILE")
from pathlib import Path

"""

    pyfile = PathExtended.tmp().joinpath(f"tmp_scripts/python/croshell/{randstr()}.py")
    pyfile.parent.mkdir(parents=True, exist_ok=True)

    title = "Reading Data"
    python_program = preprogram + add_print_header_pycode(str(pyfile), title=title) + program
    pyfile.write_text(python_program, encoding="utf-8")
    # ve_root_from_file, ipython_profile = get_ve_path_and_ipython_profile(PathExtended(file))
    ipython_profile = ipython_profile if ipython_profile is not None else "default"
    # ve_activateion_line = get_ve_activate_line(ve_name=args.ve or ve_profile_suggested, a_path=str(PathExtended.cwd()))

    if visidata:
        fire_line = f"uv run --with visidata,pyarrow vd {str(file_obj)}"
    elif jupyter:
        fire_line = f"code --new-window {str(pyfile)}"
    else:
        if interpreter == "ipython": profile = f" --profile {ipython_profile} --no-banner"
        else: profile = ""
        if local:
            from machineconfig.utils.source_of_truth import LIBRARY_ROOT
            repo_root = LIBRARY_ROOT.parent.parent
            if repo_root.parent.name == "code" and repo_root.name == "machineconfig" and repo_root.exists() and repo_root.is_dir():
                ve_line = f"--project {str(repo_root)}"
            else:
                console.print(Panel("❌ Could not determine the local machineconfig repo root. Please ensure the `REPO_ROOT` in `source_of_truth.py` is correctly set to the local path of the machineconfig repo, or do not use the `--local` flag.", title="Error", border_style="red"))
                return
        else: ve_line = "--with machineconfig[plot]>=5.6"
        fire_line = f"uv run --python 3.14 {ve_line} {interpreter} {interactivity} {profile} {str(pyfile)}"

    from machineconfig.utils.code import run_shell_script
    run_shell_script(fire_line, clean_env=False)


def arg_parser() -> None:
    typer.run(main)


if __name__ == "__main__":
    arg_parser()
