"""
setup file for each shell can be found in $profile. The settings.json is the config file for Terminal.
https://glitchbone.github.io/vscode-base16-term/#/3024

"""


from machineconfig.utils.path_reduced import P as PathExtended
from machineconfig.utils.utils import LIBRARY_ROOT
from machineconfig.utils.installer_utils.installer_class import Installer
import subprocess


nerd_fonts = {
    "repo_url": "https://github.com/ryanoasis/nerd-fonts",
    "doc": "Nerd Fonts is a project that patches developer targeted fonts with a high number of glyphs (icons)",
    "filename_template_windows_amd_64": "CascadiaCode.zip",
    "filename_template_linux_amd_64": "CascadiaCode.zip",
    "strip_v": False,
    "exe_name": "nerd_fonts"
}


def install_nerd_fonts():
    print(f"\n{'='*80}\n📦 INSTALLING NERD FONTS 📦\n{'='*80}")
    # Step 1: download the required fonts that has all the glyphs and install them.
    print("🔍 Downloading Nerd Fonts package...")
    folder, _version_to_be_installed = Installer.from_dict(d=nerd_fonts, name="nerd_fonts").download(version=None)
    
    print("🧹 Cleaning up unnecessary files...")
    folder.search("*Windows*").apply(lambda p: p.delete(sure=True))
    folder.search("*readme*").apply(lambda p: p.delete(sure=True))
    folder.search("*LICENSE*").apply(lambda p: p.delete(sure=True))
    
    print("⚙️  Installing fonts via PowerShell...")
    file = PathExtended.tmpfile(suffix=".ps1").write_text(LIBRARY_ROOT.joinpath("setup_windows/wt_and_pwsh/install_fonts.ps1").read_text().replace(r".\fonts-to-be-installed", str(folder)))
    subprocess.run(rf"powershell.exe -executionpolicy Bypass -nologo -noninteractive -File {str(file)}", check=True)
    
    print("🗑️  Cleaning up temporary files...")
    folder.delete(sure=True)
    print(f"\n✅ Nerd Fonts installation complete! ✅\n{'='*80}")


def main():
    print(f"\n{'='*80}\n🎨 POWERSHELL THEME SETUP 🎨\n{'='*80}")
    install_nerd_fonts()
    print(f"\n✅ All PowerShell theme components installed successfully! ✅\n{'='*80}")


if __name__ == '__main__':
    pass
