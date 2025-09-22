
from pathlib import Path
from machineconfig.cluster.sessions_managers.layout_types import LayoutConfig, LayoutsFile
from typing import Optional, TYPE_CHECKING
from machineconfig.utils.path import match_file_name, sanitize_path
from machineconfig.utils.path_reduced import PathExtended as PathExtended

if TYPE_CHECKING:
    from machineconfig.scripts.python.fire_jobs_args import FireJobArgs


def select_layout(layouts_json_file: Path, layout_name: Optional[str]):
    import json
    layout_file: LayoutsFile = json.loads(layouts_json_file.read_text())
    if layout_name is None:
        options = [layout["layoutName"] for layout in layout_file["layouts"]]
        from machineconfig.utils.options import choose_one_option
        layout_name = choose_one_option(options=options, prompt="Choose a layout configuration:")
    layout_chosen = next((layout for layout in layout_file["layouts"] if layout["layoutName"] == layout_name))
    return layout_chosen

def launch_layout(layout_config: LayoutConfig) -> Optional[Exception]:
    from machineconfig.cluster.sessions_managers.zellij_local import run_zellij_layout
    run_zellij_layout(layout_config=layout_config)
    return None


def handle_layout_args(args: "FireJobArgs") -> None:
    path_obj = sanitize_path(args.path)
    if not path_obj.exists():
        choice_file = match_file_name(sub_string=args.path, search_root=PathExtended.cwd(), suffixes={".json"})
    else: choice_file = path_obj
    launch_layout(layout_config=select_layout(layouts_json_file=choice_file, layout_name=args.function))
