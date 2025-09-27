"""Nerd Fonts installer - Cross-platform font installation"""

import platform
from typing import Optional
from machineconfig.utils.schemas.installer.installer_types import InstallerData


def main(installer_data: InstallerData, version: Optional[str]) -> Optional[str]:
    """Main entry point for Nerd Fonts installation.
    
    Args:
        installer_data: Installation configuration data
        version: Specific version to install (None for latest)
        
    Returns:
        For Linux/Darwin: Shell script content to execute
        For Windows: None (installation handled directly)
    """
    _ = installer_data
    print(f"""
{"=" * 150}
🔤 NERD FONTS INSTALLER | Installing programming fonts with icons
💻 Platform: {platform.system()}
🔄 Version: {"latest" if version is None else version}
{"=" * 150}
""")

    _ = version
    current_platform = platform.system()
    
    if current_platform == "Windows":
        print("🪟 Installing Nerd Fonts on Windows...")
        from machineconfig.jobs.installer.custom_dev.nerfont_windows_helper import install_nerd_fonts
        
        try:
            install_nerd_fonts()
            print(f"""
{"=" * 150}
✅ SUCCESS | Nerd Fonts installation completed successfully on Windows
💡 TIP: Restart your terminal applications to see the new fonts
{"=" * 150}
""")
            return None
        except Exception as e:
            error_msg = f"Windows Nerd Fonts installation failed: {e}"
            print(f"""
{"⚠️" * 20}
❌ ERROR | {error_msg}
💡 TIP: Try running as administrator or install manually from https://www.nerdfonts.com
{"⚠️" * 20}
""")
            raise RuntimeError(error_msg) from e
            
    elif current_platform in ["Linux", "Darwin"]:
        print(f"🐧 Installing Nerd Fonts on {current_platform} using installation script...")
        import machineconfig.jobs.installer as module
        from pathlib import Path

        program = Path(module.__file__).parent.joinpath("linux_scripts/nerdfont.sh").read_text(encoding="utf-8")
        
        print(f"""
{"=" * 150}
ℹ️  INFO | Nerd Fonts features:
🎨 Programming fonts patched with icons
🔣 Includes icons from popular sets (FontAwesome, Devicons, etc.)
🖥️  Perfect for terminals and coding environments
🧰 Works with many terminal applications and editors
{"=" * 150}
""")
        
        # Script will be executed by caller (requires user input)
        return program
        
    else:
        error_msg = f"Unsupported platform: {current_platform}"
        print(f"""
{"⚠️" * 20}
❌ ERROR | {error_msg}
💡 TIP: Supported platforms are Windows, Linux, and macOS (Darwin)
{"⚠️" * 20}
""")
        raise NotImplementedError(error_msg)


if __name__ == "__main__":
    pass
