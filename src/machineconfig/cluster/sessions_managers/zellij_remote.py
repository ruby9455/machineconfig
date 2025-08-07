#!/usr/bin/env python3
from typing import Dict, Tuple, Optional, List, Union, Any
from pathlib import Path
import logging
import json
import uuid
from datetime import datetime

from machineconfig.cluster.sessions_managers.zellij_utils.remote_executor import RemoteExecutor
from machineconfig.cluster.sessions_managers.zellij_utils.layout_generator import LayoutGenerator
from machineconfig.cluster.sessions_managers.zellij_utils.process_monitor import ProcessMonitor
from machineconfig.cluster.sessions_managers.zellij_utils.session_manager import SessionManager
from machineconfig.cluster.sessions_managers.zellij_utils.status_reporter import StatusReporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TMP_LAYOUT_DIR = Path.home().joinpath("tmp_results", "zellij_layouts", "layout_manager")


class ZellijRemoteLayoutGenerator:
    
    def __init__(self, remote_name: str, session_name_prefix: str):
        self.remote_name = remote_name
        self.session_name = session_name_prefix + "_" + LayoutGenerator.generate_random_suffix()
        self.tab_config: Dict[str, Tuple[str, str]] = {}
        self.layout_path: Optional[str] = None
        
        # Initialize modular components
        self.remote_executor = RemoteExecutor(remote_name)
        self.layout_generator = LayoutGenerator()
        self.process_monitor = ProcessMonitor(self.remote_executor)
        self.session_manager = SessionManager(self.remote_executor, self.session_name, TMP_LAYOUT_DIR)
        self.status_reporter = StatusReporter(self.process_monitor, self.session_manager)
    
    def copy_layout_to_remote(self, local_layout_file: Path, random_suffix: str) -> str:
        return self.session_manager.copy_layout_to_remote(local_layout_file, random_suffix)

    def create_zellij_layout(self, tab_config: Dict[str, Tuple[str, str]], output_dir: Optional[str] = None) -> str:
        logger.info(f"Creating Zellij layout with {len(tab_config)} tabs for remote '{self.remote_name}'")
        self.tab_config = tab_config.copy()
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = TMP_LAYOUT_DIR
        self.layout_path = self.layout_generator.create_layout_file(tab_config, output_path, self.session_name)        
        return self.layout_path
    
    def get_layout_preview(self, tab_config: Dict[str, Tuple[str, str]]) -> str:
        return self.layout_generator.generate_layout_content(tab_config)
    
    def check_command_status(self, tab_name: str, use_verification: bool = True) -> Dict[str, Any]:
        return self.process_monitor.check_command_status(tab_name, self.tab_config, use_verification)

    def check_all_commands_status(self) -> Dict[str, Dict[str, Any]]:
        return self.process_monitor.check_all_commands_status(self.tab_config)

    def check_zellij_session_status(self) -> Dict[str, Any]:
        return self.session_manager.check_zellij_session_status()

    def get_comprehensive_status(self) -> Dict[str, Any]:
        return self.status_reporter.get_comprehensive_status(self.tab_config)

    def print_status_report(self) -> None:
        self.status_reporter.print_status_report(self.tab_config)

    def start_zellij_session(self, layout_file_path: Optional[str] = None) -> Dict[str, Any]:
        return self.session_manager.start_zellij_session(layout_file_path or self.layout_path)

    def attach_to_session(self) -> None:
        self.session_manager.attach_to_session()

    # Legacy methods for backward compatibility
    def force_fresh_process_check(self, tab_name: str) -> Dict[str, Any]:
        return self.process_monitor.force_fresh_process_check(tab_name, self.tab_config)

    def verify_process_alive(self, pid: int) -> bool:
        return self.process_monitor.verify_process_alive(pid)

    def get_verified_process_status(self, tab_name: str) -> Dict[str, Any]:
        return self.process_monitor.get_verified_process_status(tab_name, self.tab_config)

    # Static methods for backward compatibility
    @staticmethod
    def run_remote_command(remote_name: str, command: str, timeout: int = 30):
        executor = RemoteExecutor(remote_name)
        return executor.run_command(command, timeout)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "remote_name": self.remote_name,
            "session_name": self.session_name,
            "tab_config": self.tab_config,
            "layout_path": self.layout_path,
            "created_at": datetime.now().isoformat(),
            "class_name": self.__class__.__name__
        }

    def to_json(self, file_path: Optional[Union[str, Path]] = None) -> str:
        # Generate file path if not provided
        if file_path is None:
            random_id = str(uuid.uuid4())[:8]
            default_dir = Path.home() / "tmp_results" / "zellij_sessions" / "serialized"
            default_dir.mkdir(parents=True, exist_ok=True)
            file_path_obj = default_dir / f"zellij_session_{random_id}.json"
        else:
            file_path_obj = Path(file_path)
        
        # Ensure .json extension
        if not str(file_path_obj).endswith('.json'):
            file_path_obj = file_path_obj.with_suffix('.json')
            
        # Ensure parent directory exists
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize to JSON
        data = self.to_dict()
        
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Serialized ZellijRemoteLayoutGenerator to: {file_path_obj}")
        return str(file_path_obj)

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> 'ZellijRemoteLayoutGenerator':
        file_path = Path(file_path)
        
        # Ensure .json extension
        if not str(file_path).endswith('.json'):
            file_path = file_path.with_suffix('.json')
            
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate that it's the correct class
        if data.get('class_name') != cls.__name__:
            logger.warning(f"Class name mismatch: expected {cls.__name__}, got {data.get('class_name')}")
        
        # Create new instance
        # Extract session name prefix by removing the suffix
        session_name = data['session_name']
        if '_' in session_name:
            session_name_prefix = '_'.join(session_name.split('_')[:-1])
        else:
            session_name_prefix = session_name
            
        instance = cls(remote_name=data['remote_name'], session_name_prefix=session_name_prefix)
        
        # Restore state
        instance.session_name = data['session_name']
        instance.tab_config = data['tab_config']
        instance.layout_path = data['layout_path']
        
        logger.info(f"✅ Loaded ZellijRemoteLayoutGenerator from: {file_path}")
        return instance

    @staticmethod
    def list_saved_sessions(directory_path: Optional[Union[str, Path]] = None) -> List[str]:
        if directory_path is None:
            directory_path = Path.home() / "tmp_results" / "zellij_sessions" / "serialized"
        else:
            directory_path = Path(directory_path)
            
        if not directory_path.exists():
            return []
        
        json_files = [f.name for f in directory_path.glob("*.json")]
        return sorted(json_files)

if __name__ == "__main__":
    # Example usage
    sample_tabs = {
        "🤖Bot1": ("~/code/bytesense/bithence", "~/scripts/fire -mO go1.py bot1 --kw create_new_bot True"),
        "🤖Bot2": ("~/code/bytesense/bithence", "~/scripts/fire -mO go2.py bot2 --kw create_new_bot True"), 
        "📊Monitor": ("~", "htop"),
        "📝Logs": ("/var/log", "tail -f /var/log/app.log")
    }
    
    # Replace 'myserver' with an actual SSH config alias
    remote_name = "myserver"  # This should be in ~/.ssh/config
    session_name = "test_remote_session"
    
    try:
        # Create layout using the remote generator
        generator = ZellijRemoteLayoutGenerator(remote_name=remote_name, session_name_prefix=session_name)
        layout_path = generator.create_zellij_layout(sample_tabs)
        print(f"✅ Remote layout created successfully: {layout_path}")
        
        # Demonstrate serialization
        print("\n💾 Demonstrating serialization...")
        saved_path = generator.to_json()
        print(f"✅ Session saved to: {saved_path}")
        
        # List all saved sessions
        saved_sessions = ZellijRemoteLayoutGenerator.list_saved_sessions()
        print(f"📋 Available saved sessions: {saved_sessions}")
        
        # Demonstrate loading (using the full path)
        loaded_generator = ZellijRemoteLayoutGenerator.from_json(saved_path)
        print(f"✅ Session loaded successfully: {loaded_generator.session_name}")
        print(f"📊 Loaded tabs: {list(loaded_generator.tab_config.keys())}")
        
        # Demonstrate status checking
        print(f"\n🔍 Checking command status on remote '{remote_name}':")
        generator.print_status_report()
        
        # Start the session (uncomment to actually start)
        # start_result = generator.start_zellij_session()
        # print(f"Session start result: {start_result}")
        
        # Attach to session (uncomment to attach)
        # generator.attach_to_session()
        
    except Exception as e:
        print(f"❌ Error: {e}")
