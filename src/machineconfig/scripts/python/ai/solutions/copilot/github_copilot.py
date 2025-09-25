from pathlib import Path

from machineconfig.scripts.python.ai.solutions._shared import get_generic_instructions_path
from machineconfig.utils.source_of_truth import LIBRARY_ROOT



def build_configuration(repo_root: Path) -> None:
    instructions_repository_dir = LIBRARY_ROOT.joinpath("scripts/python/ai/solutions/copilot/instructions")
    chatmodes_dir = LIBRARY_ROOT.joinpath("scripts/python/ai/solutions/copilot/chatmodes")
    prompts_dir = LIBRARY_ROOT.joinpath("scripts/python/ai/solutions/copilot/prompts")

    github_dir = repo_root.joinpath(".github")
    chatmodes_target_dir = github_dir.joinpath("chatmodes")
    prompts_target_dir = github_dir.joinpath("prompts")
    instructions_target_dir = github_dir.joinpath("instructions")

    chatmodes_target_dir.mkdir(parents=True, exist_ok=True)
    prompts_target_dir.mkdir(parents=True, exist_ok=True)
    instructions_target_dir.mkdir(parents=True, exist_ok=True)

    for chatmode in chatmodes_dir.iterdir():
        chatmode_target = chatmodes_target_dir.joinpath(f"{chatmode.name.split('.')[0]}.chatmode.md")
        chatmode_target.write_text(data=chatmode.read_text(encoding="utf-8"), encoding="utf-8")

    for prompt in prompts_dir.iterdir():
        prompt_target = prompts_target_dir.joinpath(f"{prompt.name.split('.')[0]}.prompt.md")
        prompt_target.write_text(data=prompt.read_text(encoding="utf-8"), encoding="utf-8")

    for instruction in instructions_repository_dir.rglob("*.md"):
        instruction_target = instructions_target_dir.joinpath(f"{instruction.name.split('.')[0]}.instruction.md")
        instruction_target.write_text(data=instruction.read_text(encoding="utf-8"), encoding="utf-8")

    generic_instructions_path = get_generic_instructions_path()
    github_dir.joinpath("copilot-instructions.md").write_text(data=generic_instructions_path.read_text(encoding="utf-8"), encoding="utf-8")
