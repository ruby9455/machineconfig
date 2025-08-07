#!/usr/bin/env python3
"""
Windows Terminal layout generation utilities for creating wt command strings.
Based on Windows Terminal documentation: https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments
"""
import shlex
import random
import string
from typing import Dict, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WTLayoutGenerator:
    """Handles generation of Windows Terminal command strings for multi-tab layouts."""
    
    @staticmethod
    def generate_random_suffix(length: int = 8) -> str:
        """Generate a random string suffix for unique window names."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @staticmethod
    def parse_command(command: str) -> Tuple[str, List[str]]:
        """Parse a command string into command and arguments."""
        try:
            parts = shlex.split(command)
            if not parts: 
                raise ValueError("Empty command provided")
            return parts[0], parts[1:] if len(parts) > 1 else []
        except ValueError as e:
            logger.error(f"Error parsing command '{command}': {e}")
            parts = command.split()
            return parts[0] if parts else "", parts[1:] if len(parts) > 1 else []
    
    @staticmethod
    def escape_for_wt(text: str) -> str:
        """Escape text for use in Windows Terminal commands."""
        # Windows Terminal uses PowerShell-style escaping
        # Escape special characters that might cause issues
        text = text.replace('"', '""')  # Escape quotes for PowerShell
        if ' ' in text or ';' in text or '&' in text or '|' in text:
            return f'"{text}"'
        return text
    
    @staticmethod
    def create_tab_command(tab_name: str, cwd: str, command: str, is_first_tab: bool = False) -> str:
        """Create a Windows Terminal tab command string."""
        cmd, args = WTLayoutGenerator.parse_command(command)
        
        # Convert paths to Windows format if needed
        if cwd.startswith('~/'):
            cwd = cwd.replace('~/', f"{Path.home()}/")
        elif cwd == '~':
            cwd = str(Path.home())
        
        # Build the wt command parts
        tab_parts = []
        
        if not is_first_tab:
            tab_parts.append("new-tab")
        
        # Add profile if specified (could be extended to support different shells)
        # tab_parts.extend(["-p", "\"Command Prompt\""])  # or "PowerShell", "WSL", etc.
        
        # Add starting directory
        tab_parts.extend(["-d", WTLayoutGenerator.escape_for_wt(cwd)])
        
        # Add tab title
        tab_parts.extend(["--title", WTLayoutGenerator.escape_for_wt(tab_name)])
        
        # Add the command to execute
        full_command = command if not args else f"{cmd} {' '.join(args)}"
        tab_parts.append(WTLayoutGenerator.escape_for_wt(full_command))
        
        return " ".join(tab_parts)
    
    @staticmethod
    def validate_tab_config(tab_config: Dict[str, Tuple[str, str]]) -> None:
        """Validate tab configuration format and content."""
        if not tab_config: 
            raise ValueError("Tab configuration cannot be empty")
        for tab_name, (cwd, command) in tab_config.items():
            if not tab_name.strip(): 
                raise ValueError(f"Invalid tab name: {tab_name}")
            if not command.strip(): 
                raise ValueError(f"Invalid command for tab '{tab_name}': {command}")
            if not cwd.strip(): 
                raise ValueError(f"Invalid cwd for tab '{tab_name}': {cwd}")
    
    def generate_wt_command(self, tab_config: Dict[str, Tuple[str, str]], 
                           window_name: str | None = None, 
                           maximized: bool = False,
                           focus: bool = True) -> str:
        """Generate complete Windows Terminal command string."""
        self.validate_tab_config(tab_config)
        
        # Start building the wt command
        wt_parts = ["wt"]
        
        # Add window options
        if maximized:
            wt_parts.append("--maximized")
        
        if focus:
            wt_parts.append("--focus")
        
        if window_name:
            wt_parts.extend(["-w", WTLayoutGenerator.escape_for_wt(window_name)])
        
        # Add tabs
        tab_commands = []
        for i, (tab_name, (cwd, command)) in enumerate(tab_config.items()):
            is_first = i == 0
            tab_cmd = self.create_tab_command(tab_name, cwd, command, is_first)
            tab_commands.append(tab_cmd)
        
        # Join all parts with semicolons (Windows Terminal command separator)
        if tab_commands:
            if len(tab_commands) == 1:
                # Single tab - just add to the main command
                wt_parts.extend(tab_commands[0].split())
            else:
                # Multiple tabs - join with semicolons
                wt_parts.append(tab_commands[0])  # First tab
                for tab_cmd in tab_commands[1:]:
                    wt_parts.extend([";", tab_cmd])
        
        return " ".join(wt_parts)
    
    def create_wt_script(self, tab_config: Dict[str, Tuple[str, str]], 
                        output_dir: Path, session_name: str,
                        window_name: str | None = None) -> str:
        """Create a Windows Terminal script file and return its absolute path."""
        self.validate_tab_config(tab_config)
        
        # Generate unique suffix for this script
        random_suffix = self.generate_random_suffix()
        wt_command = self.generate_wt_command(tab_config, window_name or session_name)
        
        try:
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create both .bat and .ps1 versions for flexibility
            bat_file = output_dir / f"wt_layout_{session_name}_{random_suffix}.bat"
            ps1_file = output_dir / f"wt_layout_{session_name}_{random_suffix}.ps1"
            
            # Create batch file
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write(f"@echo off\n")
                f.write(f"REM Windows Terminal layout for {session_name}\n")
                f.write(f"{wt_command}\n")
            
            # Create PowerShell file (better for complex commands)
            with open(ps1_file, 'w', encoding='utf-8') as f:
                f.write(f"# Windows Terminal layout for {session_name}\n")
                f.write(f"# Generated on {random_suffix}\n")
                f.write(f"{wt_command}\n")
            
            logger.info(f"Windows Terminal script files created: {bat_file.absolute()}")
            return str(bat_file.absolute())
            
        except OSError as e:
            logger.error(f"Failed to create script file: {e}")
            raise
    
    def generate_split_pane_command(self, tab_config: Dict[str, Tuple[str, str]], 
                                   window_name: str | None = None) -> str:
        """Generate Windows Terminal command with split panes instead of separate tabs."""
        self.validate_tab_config(tab_config)
        
        wt_parts = ["wt"]
        
        if window_name:
            wt_parts.extend(["-w", WTLayoutGenerator.escape_for_wt(window_name)])
        
        # First pane (main tab)
        first_tab = list(tab_config.items())[0]
        tab_name, (cwd, command) = first_tab
        
        # Start with first tab
        wt_parts.extend(["-d", WTLayoutGenerator.escape_for_wt(cwd)])
        wt_parts.extend(["--title", WTLayoutGenerator.escape_for_wt(tab_name)])
        wt_parts.append(WTLayoutGenerator.escape_for_wt(command))
        
        # Add split panes for remaining tabs
        for tab_name, (cwd, command) in list(tab_config.items())[1:]:
            wt_parts.append(";")
            wt_parts.append("split-pane")
            wt_parts.extend(["-d", WTLayoutGenerator.escape_for_wt(cwd)])
            wt_parts.extend(["--title", WTLayoutGenerator.escape_for_wt(tab_name)])
            wt_parts.append(WTLayoutGenerator.escape_for_wt(command))
        
        return " ".join(wt_parts) 