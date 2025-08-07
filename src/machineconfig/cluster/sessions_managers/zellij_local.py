#!/usr/bin/env python3
import shlex
import subprocess
import psutil
import random
import string
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TMP_LAYOUT_DIR = Path.home().joinpath("tmp_results", "session_manager", "zellij", "layout_manager")


class ZellijLayoutGenerator:
    def __init__(self):
        self.session_name: Optional[str] = None
        self.tab_config: Dict[str, tuple[str, str]] = {}  # Store entire tab config (cwd, command) for status checking
        self.layout_path: Optional[str] = None  # Store the full path to the layout file
        self.layout_template = """layout {
    default_tab_template {
        // the default zellij tab-bar and status bar plugins
        pane size=1 borderless=true {
            plugin location="zellij:compact-bar"
        }
        children
    }
"""
    
    @staticmethod
    def _generate_random_suffix(length: int = 8) -> str:
        """Generate a random string suffix for unique layout file names."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @staticmethod
    def _parse_command(command: str) -> tuple[str, List[str]]:
        try:
            parts = shlex.split(command)
            if not parts: raise ValueError("Empty command provided")
            return parts[0], parts[1:] if len(parts) > 1 else []
        except ValueError as e:
            logger.error(f"Error parsing command '{command}': {e}")
            parts = command.split()
            return parts[0] if parts else "", parts[1:] if len(parts) > 1 else []
    
    @staticmethod
    def _format_args_for_kdl(args: List[str]) -> str:
        if not args: return ""
        formatted_args = []
        for arg in args:
            if ' ' in arg or '"' in arg or "'" in arg:
                escaped_arg = arg.replace('"', '\\"')
                formatted_args.append(f'"{escaped_arg}"')
            else:
                formatted_args.append(f'"{arg}"')
        return " ".join(formatted_args)
    
    @staticmethod
    def _create_tab_section(tab_name: str, cwd: str, command: str) -> str:
        cmd, args = ZellijLayoutGenerator._parse_command(command)
        args_str = ZellijLayoutGenerator._format_args_for_kdl(args)
        tab_cwd = cwd or "~"
        escaped_tab_name = tab_name.replace('"', '\\"')
        tab_section = f'  tab name="{escaped_tab_name}" cwd="{tab_cwd}" {{\n'
        tab_section += f'    pane command="{cmd}" {{\n'
        if args_str: tab_section += f'      args {args_str}\n'
        tab_section += '    }\n  }\n'
        return tab_section
    
    @staticmethod
    def _validate_tab_config(tab_config: Dict[str, tuple[str, str]]) -> None:
        if not tab_config: raise ValueError("Tab configuration cannot be empty")
        for tab_name, (cwd, command) in tab_config.items():
            if not tab_name.strip(): raise ValueError(f"Invalid tab name: {tab_name}")
            if not command.strip(): raise ValueError(f"Invalid command for tab '{tab_name}': {command}")
            if not cwd.strip(): raise ValueError(f"Invalid cwd for tab '{tab_name}': {cwd}")
    
    def create_zellij_layout(self, tab_config: Dict[str, tuple[str, str]], output_dir: Optional[str] = None, session_name: Optional[str] = None) -> str:
        ZellijLayoutGenerator._validate_tab_config(tab_config)
        logger.info(f"Creating Zellij layout with {len(tab_config)} tabs")
        
        # Store session name and entire tab config for status checking
        self.session_name = session_name or "default"
        self.tab_config = tab_config.copy()
        
        layout_content = self.layout_template
        for tab_name, (cwd, command) in tab_config.items():
            layout_content += "\n" + ZellijLayoutGenerator._create_tab_section(tab_name, cwd, command)
        layout_content += "\n}\n"
        try:
            random_suffix = ZellijLayoutGenerator._generate_random_suffix()
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                layout_file = output_path / f"zellij_layout_{random_suffix}.kdl"
                with open(layout_file, 'w', encoding='utf-8') as f:
                    f.write(layout_content)
                self.layout_path = str(layout_file.absolute())
            else:
                # Use the predefined TMP_LAYOUT_DIR for temporary files
                TMP_LAYOUT_DIR.mkdir(parents=True, exist_ok=True)
                layout_file = TMP_LAYOUT_DIR / f"zellij_layout_{self.session_name or 'default'}_{random_suffix}.kdl"
                with open(layout_file, 'w', encoding='utf-8') as f:
                    f.write(layout_content)
                self.layout_path = str(layout_file.absolute())
            logger.info(f"Zellij layout file created: {self.layout_path}")
            return self.layout_path
        except OSError as e:
            logger.error(f"Failed to create layout file: {e}")
            raise
    
    @staticmethod
    def get_layout_preview(tab_config: Dict[str, tuple[str, str]], layout_template: str | None = None) -> str:
        if layout_template is None:
            layout_template = """layout {
    default_tab_template {
        // the default zellij tab-bar and status bar plugins
        pane size=1 borderless=true {
            plugin location="zellij:compact-bar"
        }
        children
    }
"""
        ZellijLayoutGenerator._validate_tab_config(tab_config)
        layout_content = layout_template
        for tab_name, (cwd, command) in tab_config.items():
            layout_content += "\n" + ZellijLayoutGenerator._create_tab_section(tab_name, cwd, command)
        return layout_content + "\n}\n"
    
    @staticmethod
    def check_command_status(tab_name: str, tab_config: Dict[str, tuple[str, str]]) -> Dict[str, Any]:
        if tab_name not in tab_config:
            return {
                "status": "unknown",
                "error": f"Tab '{tab_name}' not found in tracked tab config",
                "running": False,
                "pid": None,
                "command": None,
                "cwd": None
            }
        
        cwd, command = tab_config[tab_name]
        cmd, _ = ZellijLayoutGenerator._parse_command(command)
        
        try:
            # Look for processes matching the command
            matching_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                try:
                    if proc.info['cmdline'] and len(proc.info['cmdline']) > 0:
                        # Check if the command matches
                        if (proc.info['name'] == cmd or 
                            cmd in proc.info['cmdline'][0] or
                            any(cmd in arg for arg in proc.info['cmdline'])):
                            matching_processes.append({
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "cmdline": proc.info['cmdline'],
                                "status": proc.info['status']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if matching_processes:
                return {
                    "status": "running",
                    "running": True,
                    "processes": matching_processes,
                    "command": command,
                    "cwd": cwd,
                    "tab_name": tab_name
                }
            else:
                return {
                    "status": "not_running",
                    "running": False,
                    "processes": [],
                    "command": command,
                    "cwd": cwd,
                    "tab_name": tab_name
                }
                
        except Exception as e:
            logger.error(f"Error checking command status for tab '{tab_name}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "running": False,
                "command": command,
                "cwd": cwd,
                "tab_name": tab_name
            }

    def check_all_commands_status(self) -> Dict[str, Dict[str, Any]]:
        if not self.tab_config:
            logger.warning("No tab config tracked. Make sure to create a layout first.")
            return {}
        
        status_report = {}
        for tab_name in self.tab_config:
            status_report[tab_name] = ZellijLayoutGenerator.check_command_status(tab_name, self.tab_config)
        
        return status_report

    @staticmethod
    def check_zellij_session_status(session_name: str) -> Dict[str, Any]:
        try:
            # Run zellij list-sessions command
            result = subprocess.run(
                ['zellij', 'list-sessions'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                sessions = result.stdout.strip().split('\n') if result.stdout.strip() else []
                session_running = any(session_name in session for session in sessions)
                
                return {
                    "zellij_running": True,
                    "session_exists": session_running,
                    "session_name": session_name,
                    "all_sessions": sessions
                }
            else:
                return {
                    "zellij_running": False,
                    "error": result.stderr,
                    "session_name": session_name
                }
                
        except subprocess.TimeoutExpired:
            return {
                "zellij_running": False,
                "error": "Timeout while checking Zellij sessions",
                "session_name": session_name
            }
        except FileNotFoundError:
            return {
                "zellij_running": False,
                "error": "Zellij not found in PATH",
                "session_name": session_name
            }
        except Exception as e:
            return {
                "zellij_running": False,
                "error": str(e),
                "session_name": session_name
            }

    def get_comprehensive_status(self) -> Dict[str, Any]:
        zellij_status = ZellijLayoutGenerator.check_zellij_session_status(self.session_name or "default")
        commands_status = self.check_all_commands_status()
        
        running_count = sum(1 for status in commands_status.values() if status.get("running", False))
        total_count = len(commands_status)
        
        return {
            "zellij_session": zellij_status,
            "commands": commands_status,
            "summary": {
                "total_commands": total_count,
                "running_commands": running_count,
                "stopped_commands": total_count - running_count,
                "session_healthy": zellij_status.get("session_exists", False)
            }
        }

    def print_status_report(self) -> None:
        status = self.get_comprehensive_status()
        
        print("=" * 60)
        print("🔍 ZELLIJ LAYOUT STATUS REPORT")
        print("=" * 60)
        
        # Zellij session status
        zellij = status["zellij_session"]
        if zellij.get("zellij_running", False):
            if zellij.get("session_exists", False):
                print(f"✅ Zellij session '{self.session_name}' is running")
            else:
                print(f"⚠️  Zellij is running but session '{self.session_name}' not found")
        else:
            print(f"❌ Zellij session issue: {zellij.get('error', 'Unknown error')}")
        
        print()
        
        # Commands status
        print("📋 COMMAND STATUS:")
        print("-" * 40)
        
        for tab_name, cmd_status in status["commands"].items():
            if cmd_status.get("running", False):
                print(f"✅ {tab_name}: Running")
                if cmd_status.get("processes"):
                    for proc in cmd_status["processes"][:2]:  # Show first 2 processes
                        print(f"   └─ PID {proc['pid']}: {proc['name']} ({proc['status']})")
            else:
                print(f"❌ {tab_name}: Not running")
            print(f"   Command: {cmd_status.get('command', 'Unknown')}")
            print()
        
        # Summary
        summary = status["summary"]
        print("📊 SUMMARY:")
        print(f"   Total commands: {summary['total_commands']}")
        print(f"   Running: {summary['running_commands']}")
        print(f"   Stopped: {summary['stopped_commands']}")
        print(f"   Session healthy: {'✅' if summary['session_healthy'] else '❌'}")
        print("=" * 60)

def created_zellij_layout(tab_config: Dict[str, tuple[str, str]], output_dir: Optional[str] = None) -> str:
    generator = ZellijLayoutGenerator()
    return generator.create_zellij_layout(tab_config, output_dir)
def run_zellij_layout(tab_config: Dict[str, tuple[str, str]], session_name: Optional[str] = None) -> str:
    if not session_name:
        session_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    layout_path = created_zellij_layout(tab_config)
    cmd = f"zellij delete-session --force {session_name}; zellij --layout {layout_path} a -b {session_name}"
    import subprocess
    subprocess.run(cmd, shell=True, check=True)
    print(f"zellij layout is running @ {session_name}")
    return session_name


def run_command_in_zellij_tab(command: str, tab_name: str, cwd: Optional[str]) -> str:
    maybe_cwd = f"--cwd {cwd}" if cwd is not None else ""
    return f"""
echo "Sleep 1 seconds to allow zellij to create a new tab"
sleep 1
zellij action new-tab --name {tab_name} {maybe_cwd}
echo "Sleep 2 seconds to allow zellij to go to the new tab"
sleep 2
zellij action go-to-tab-name {tab_name}
echo "Sleep 2 seconds to allow zellij to start the new pane"
sleep 2
zellij action new-pane --direction down -- /bin/bash {command}
echo "Sleep 2 seconds to allow zellij to start the new pane"
sleep 1
zellij action move-focus up; sleep 2
echo "Sleep 2 seconds to allow zellij to close the pane"
sleep 1
zellij action close-pane; sleep 2
"""


if __name__ == "__main__":
    sample_tabs = {
        "🤖Bot1": ("~/code/bytesense/bithence", "~/scripts/fire -mO go1.py bot1 --kw create_new_bot True"),
        "🤖Bot2": ("~/code/bytesense/bithence", "~/scripts/fire -mO go2.py bot2 --kw create_new_bot True"), 
        "📊Monitor": ("~", "htop"),
        "📝Logs": ("/var/log", "tail -f /var/log/app.log")
    }
    try:
        # Create layout using the generator directly to access status methods
        generator = ZellijLayoutGenerator()
        layout_path = generator.create_zellij_layout(sample_tabs, session_name="test_session")
        print(f"✅ Layout created successfully: {layout_path}")
        
        # Demonstrate status checking
        print("\n🔍 Checking command status (this is just a demo - commands aren't actually running):")
        generator.print_status_report()
        
        # Individual command status check
        print("\n🔎 Individual command status for Bot1:")
        bot1_status = ZellijLayoutGenerator.check_command_status("🤖Bot1", generator.tab_config)
        print(f"Status: {bot1_status['status']}")
        print(f"Running: {bot1_status['running']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
