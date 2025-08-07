#!/usr/bin/env python3
from datetime import datetime
import json
import uuid
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any
from crocodile.meta import Scheduler
from machineconfig.cluster.sessions_managers.zellij_local import ZellijLayoutGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TMP_SERIALIZATION_DIR = Path.home().joinpath("tmp_results", "session_manager", "zellij", "local_manager")


class ZellijLocalManager:
    """Manages multiple local zellij sessions and monitors their tabs and processes."""
    
    def __init__(self, session2zellij_tabs: Dict[str, Dict[str, tuple[str, str]]], session_name_prefix: str = "LocalJobMgr"):
        """
        Initialize the local zellij manager.
        
        Args:
            session2zellij_tabs: Dict mapping session names to their tab configs
                Format: {session_name: {tab_name: (cwd, command), ...}, ...}
            session_name_prefix: Prefix for session names
        """
        self.session_name_prefix = session_name_prefix
        self.session2zellij_tabs = session2zellij_tabs  # Store the original config
        self.managers: List[ZellijLayoutGenerator] = []
        
        # Create a ZellijLayoutGenerator for each session
        for session_name, tab_config in session2zellij_tabs.items():
            manager = ZellijLayoutGenerator()
            full_session_name = f"{self.session_name_prefix}_{session_name}"
            manager.create_zellij_layout(tab_config=tab_config, session_name=full_session_name)
            self.managers.append(manager)
        
        logger.info(f"Initialized ZellijLocalManager with {len(self.managers)} sessions")

    def get_all_session_names(self) -> List[str]:
        """Get all managed session names."""
        return [manager.session_name for manager in self.managers if manager.session_name is not None]

    def start_all_sessions(self) -> Dict[str, Any]:
        """Start all zellij sessions with their layouts."""
        results = {}
        for manager in self.managers:
            try:
                session_name = manager.session_name
                if session_name is None:
                    continue  # Skip managers without a session name
                    
                layout_path = manager.layout_path
                
                if not layout_path:
                    results[session_name] = {
                        "success": False,
                        "error": "No layout file path available"
                    }
                    continue
                
                # Delete existing session if it exists, then start with layout
                cmd = f"zellij delete-session --force {session_name}; zellij --layout {layout_path} attach {session_name} --create"
                
                logger.info(f"Starting session '{session_name}' with layout: {layout_path}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    results[session_name] = {
                        "success": True,
                        "message": f"Session '{session_name}' started successfully"
                    }
                    logger.info(f"✅ Session '{session_name}' started successfully")
                else:
                    results[session_name] = {
                        "success": False,
                        "error": result.stderr or result.stdout
                    }
                    logger.error(f"❌ Failed to start session '{session_name}': {result.stderr}")
                    
            except Exception as e:
                # Use a fallback key since session_name might not be defined here
                try:
                    key = getattr(manager, 'session_name', None) or f"manager_{self.managers.index(manager)}"
                except Exception:
                    key = f"manager_{self.managers.index(manager)}"
                results[key] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ Exception starting session '{key}': {e}")
        
        return results

    def kill_all_sessions(self) -> Dict[str, Any]:
        """Kill all managed zellij sessions."""
        results = {}
        for manager in self.managers:
            try:
                session_name = manager.session_name
                if session_name is None:
                    continue  # Skip managers without a session name
                    
                cmd = f"zellij delete-session --force {session_name}"
                
                logger.info(f"Killing session '{session_name}'")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                results[session_name] = {
                    "success": result.returncode == 0,
                    "message": "Session killed" if result.returncode == 0 else result.stderr
                }
                
            except Exception as e:
                # Use a fallback key since session_name might not be defined here
                key = getattr(manager, 'session_name', None) or f"manager_{self.managers.index(manager)}"
                results[key] = {
                    "success": False,
                    "error": str(e)
                }
                
        return results

    def attach_to_session(self, session_name: Optional[str] = None) -> str:
        """
        Generate command to attach to a specific session or list attachment commands for all.
        
        Args:
            session_name: Specific session to attach to, or None for all sessions
            
        Returns:
            Command string to attach to session(s)
        """
        if session_name:
            # Find the specific session
            for manager in self.managers:
                if manager.session_name == session_name:
                    return f"zellij attach {session_name}"
            raise ValueError(f"Session '{session_name}' not found")
        else:
            # Return commands for all sessions
            commands = []
            for manager in self.managers:
                commands.append(f"# Attach to session '{manager.session_name}':")
                commands.append(f"zellij attach {manager.session_name}")
                commands.append("")
            return "\n".join(commands)

    def check_all_sessions_status(self) -> Dict[str, Dict[str, Any]]:
        """Check the status of all sessions and their commands."""
        status_report = {}
        
        for manager in self.managers:
            session_name = manager.session_name
            if session_name is None:
                continue  # Skip managers without a session name
            
            # Get session status
            session_status = ZellijLayoutGenerator.check_zellij_session_status(session_name)
            
            # Get commands status for this session
            commands_status = manager.check_all_commands_status()
            
            # Calculate summary for this session
            running_count = sum(1 for status in commands_status.values() if status.get("running", False))
            total_count = len(commands_status)
            
            status_report[session_name] = {
                "session_status": session_status,
                "commands_status": commands_status,
                "summary": {
                    "total_commands": total_count,
                    "running_commands": running_count,
                    "stopped_commands": total_count - running_count,
                    "session_healthy": session_status.get("session_exists", False)
                }
            }
        
        return status_report

    def get_global_summary(self) -> Dict[str, Any]:
        """Get a global summary across all sessions."""
        all_status = self.check_all_sessions_status()
        
        total_sessions = len(all_status)
        healthy_sessions = sum(1 for status in all_status.values() 
                             if status["summary"]["session_healthy"])
        total_commands = sum(status["summary"]["total_commands"] 
                           for status in all_status.values())
        total_running = sum(status["summary"]["running_commands"] 
                          for status in all_status.values())
        
        return {
            "total_sessions": total_sessions,
            "healthy_sessions": healthy_sessions,
            "unhealthy_sessions": total_sessions - healthy_sessions,
            "total_commands": total_commands,
            "running_commands": total_running,
            "stopped_commands": total_commands - total_running,
            "all_sessions_healthy": healthy_sessions == total_sessions,
            "all_commands_running": total_running == total_commands
        }

    def print_status_report(self) -> None:
        """Print a comprehensive status report for all sessions."""
        all_status = self.check_all_sessions_status()
        global_summary = self.get_global_summary()
        
        print("=" * 80)
        print("🔍 ZELLIJ LOCAL MANAGER STATUS REPORT")
        print("=" * 80)
        
        # Global summary
        print("🌐 GLOBAL SUMMARY:")
        print(f"   Total sessions: {global_summary['total_sessions']}")
        print(f"   Healthy sessions: {global_summary['healthy_sessions']}")
        print(f"   Total commands: {global_summary['total_commands']}")
        print(f"   Running commands: {global_summary['running_commands']}")
        print(f"   All healthy: {'✅' if global_summary['all_sessions_healthy'] else '❌'}")
        print()
        
        # Per-session details
        for session_name, status in all_status.items():
            session_status = status["session_status"]
            commands_status = status["commands_status"]
            summary = status["summary"]
            
            print(f"📋 SESSION: {session_name}")
            print("-" * 60)
            
            # Session health
            if session_status.get("session_exists", False):
                print("✅ Session is running")
            else:
                print(f"❌ Session not found: {session_status.get('error', 'Unknown error')}")
            
            # Commands in this session
            print(f"   Commands ({summary['running_commands']}/{summary['total_commands']} running):")
            for tab_name, cmd_status in commands_status.items():
                status_icon = "✅" if cmd_status.get("running", False) else "❌"
                print(f"     {status_icon} {tab_name}: {cmd_status.get('command', 'Unknown')}")
                
                if cmd_status.get("processes"):
                    for proc in cmd_status["processes"][:2]:  # Show first 2 processes
                        print(f"        └─ PID {proc['pid']}: {proc['name']} ({proc['status']})")
            print()
        
        print("=" * 80)

    def run_monitoring_routine(self, wait_time: str = "30s") -> None:
        """
        Run a continuous monitoring routine that checks status periodically.
        
        Args:
            wait_time: How long to wait between checks (e.g., "30s", "1m", "2m")
        """
        def routine(scheduler: Scheduler):
            print(f"\n⏰ Monitoring cycle {scheduler.cycle} at {datetime.now()}")
            print("-" * 50)
            
            if scheduler.cycle % 2 == 0:
                # Detailed status check every other cycle
                all_status = self.check_all_sessions_status()
                
                # Create DataFrame for easier viewing
                status_data = []
                for session_name, status in all_status.items():
                    for tab_name, cmd_status in status["commands_status"].items():
                        status_data.append({
                            "session": session_name,
                            "tab": tab_name,
                            "running": cmd_status.get("running", False),
                            "command": cmd_status.get("command", "Unknown")[:50] + "..." if len(cmd_status.get("command", "")) > 50 else cmd_status.get("command", ""),
                            "processes": len(cmd_status.get("processes", []))
                        })
                
                if status_data:
                    # Format data as table
                    if status_data:
                        # Create header
                        headers = list(status_data[0].keys()) if status_data else []
                        header_line = " | ".join(f"{h:<15}" for h in headers)
                        separator = "-" * len(header_line)
                        print(header_line)
                        print(separator)
                        for row in status_data:
                            values = [str(row.get(h, ""))[:15] for h in headers]
                            print(" | ".join(f"{v:<15}" for v in values))
                    
                    # Check if all sessions have stopped
                    running_count = sum(1 for row in status_data if row.get("running", False))
                    if running_count == 0:
                        print("\n⚠️  All commands have stopped. Stopping monitoring.")
                        scheduler.max_cycles = scheduler.cycle
                        return
                else:
                    print("No status data available")
            else:
                # Quick summary check
                global_summary = self.get_global_summary()
                print(f"📊 Quick Summary: {global_summary['running_commands']}/{global_summary['total_commands']} commands running across {global_summary['healthy_sessions']}/{global_summary['total_sessions']} sessions")
        
        logger.info(f"Starting monitoring routine with {wait_time} intervals")
        sched = Scheduler(routine=routine, wait=wait_time)
        sched.run()

    def save(self, session_id: Optional[str] = None) -> str:
        """Save the manager state to disk."""
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
        
        # Create session directory
        session_dir = TMP_SERIALIZATION_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the session2zellij_tabs configuration
        config_file = session_dir / "session2zellij_tabs.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.session2zellij_tabs, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        metadata = {
            "session_name_prefix": self.session_name_prefix,
            "created_at": str(datetime.now()),
            "num_managers": len(self.managers),
            "sessions": list(self.session2zellij_tabs.keys()),
            "manager_type": "ZellijLocalManager"
        }
        metadata_file = session_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Save each manager's state
        managers_dir = session_dir / "managers"
        managers_dir.mkdir(exist_ok=True)
        
        for i, manager in enumerate(self.managers):
            manager_data = {
                "session_name": manager.session_name,
                "tab_config": manager.tab_config,
                "layout_path": manager.layout_path
            }
            manager_file = managers_dir / f"manager_{i}_{manager.session_name}.json"
            with open(manager_file, 'w', encoding='utf-8') as f:
                json.dump(manager_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved ZellijLocalManager session to: {session_dir}")
        return session_id

    @classmethod
    def load(cls, session_id: str) -> 'ZellijLocalManager':
        """Load a saved manager state from disk."""
        session_dir = TMP_SERIALIZATION_DIR / session_id
        
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")
        
        # Load configuration
        config_file = session_dir / "session2zellij_tabs.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            session2zellij_tabs = json.load(f)
        
        # Load metadata
        metadata_file = session_dir / "metadata.json"
        session_name_prefix = "LocalJobMgr"  # default fallback
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                session_name_prefix = metadata.get("session_name_prefix", "LocalJobMgr")
        
        # Create new instance
        instance = cls(session2zellij_tabs=session2zellij_tabs, session_name_prefix=session_name_prefix)
        
        # Load saved manager states
        managers_dir = session_dir / "managers"
        if managers_dir.exists():
            instance.managers = []
            manager_files = sorted(managers_dir.glob("manager_*.json"))
            
            for manager_file in manager_files:
                try:
                    with open(manager_file, 'r', encoding='utf-8') as f:
                        manager_data = json.load(f)
                    
                    # Recreate the manager
                    manager = ZellijLayoutGenerator()
                    manager.session_name = manager_data["session_name"]
                    manager.tab_config = manager_data["tab_config"]
                    manager.layout_path = manager_data["layout_path"]
                    
                    instance.managers.append(manager)
                    
                except Exception as e:
                    logger.warning(f"Failed to load manager from {manager_file}: {e}")
        
        logger.info(f"✅ Loaded ZellijLocalManager session from: {session_dir}")
        return instance

    @staticmethod
    def list_saved_sessions() -> List[str]:
        """List all saved session IDs."""
        if not TMP_SERIALIZATION_DIR.exists():
            return []
        
        sessions = []
        for item in TMP_SERIALIZATION_DIR.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                sessions.append(item.name)
        
        return sorted(sessions)

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a saved session."""
        session_dir = TMP_SERIALIZATION_DIR / session_id
        
        if not session_dir.exists():
            logger.warning(f"Session directory not found: {session_dir}")
            return False
        
        try:
            import shutil
            shutil.rmtree(session_dir)
            logger.info(f"✅ Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List currently active zellij sessions managed by this instance."""
        active_sessions = []
        
        try:
            # Get all running zellij sessions
            result = subprocess.run(
                ['zellij', 'list-sessions'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                all_sessions = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                # Filter to only our managed sessions
                for manager in self.managers:
                    session_name = manager.session_name
                    if session_name is None:
                        continue  # Skip managers without a session name
                    is_active = any(session_name in session for session in all_sessions)
                    
                    active_sessions.append({
                        "session_name": session_name,
                        "is_active": is_active,
                        "tab_count": len(manager.tab_config),
                        "tabs": list(manager.tab_config.keys())
                    })
            
        except Exception as e:
            logger.error(f"Error listing active sessions: {e}")
        
        return active_sessions


if __name__ == "__main__":
    # Example usage
    sample_sessions = {
        "development": {
            "🚀Frontend": ("~/code/myapp/frontend", "npm run dev"),
            "⚙️Backend": ("~/code/myapp/backend", "python manage.py runserver"),
            "📊Monitor": ("~", "htop")
        },
        "testing": {
            "🧪Tests": ("~/code/myapp", "pytest --watch"),
            "🔍Coverage": ("~/code/myapp", "coverage run --source=. -m pytest"),
            "📝Logs": ("~/logs", "tail -f app.log")
        },
        "deployment": {
            "🐳Docker": ("~/code/myapp", "docker-compose up"),
            "☸️K8s": ("~/k8s", "kubectl get pods --watch"),
            "📈Metrics": ("~", "k9s")
        }
    }
    
    try:
        # Create the local manager
        manager = ZellijLocalManager(sample_sessions, session_name_prefix="DevEnv")
        print(f"✅ Local manager created with {len(manager.managers)} sessions")
        
        # Show session names
        print(f"📋 Sessions: {manager.get_all_session_names()}")
        
        # Print attachment commands (without actually starting)
        print("\n📎 Attachment commands:")
        print(manager.attach_to_session())
        
        # Show current status
        print("\n🔍 Current status:")
        manager.print_status_report()
        
        # Demonstrate save/load
        print("\n💾 Demonstrating save/load...")
        session_id = manager.save()
        print(f"✅ Saved session: {session_id}")
        
        # List saved sessions
        saved_sessions = ZellijLocalManager.list_saved_sessions()
        print(f"📋 Saved sessions: {saved_sessions}")
        
        # Load and verify
        loaded_manager = ZellijLocalManager.load(session_id)
        print(f"✅ Loaded session with {len(loaded_manager.managers)} sessions")
        
        # Show how to start monitoring (commented out to prevent infinite loop in demo)
        print("\n⏰ To start monitoring, run:")
        print("manager.run_monitoring_routine(wait_time='30s')")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc() 