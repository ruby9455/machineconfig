from machineconfig.utils.path_extended import PathExtended as PathExtended
from machineconfig.utils.installer_utils.installer_abc import find_move_delete_linux, find_move_delete_windows
from machineconfig.utils.source_of_truth import INSTALL_TMP_DIR, INSTALL_VERSION_ROOT, LIBRARY_ROOT
from machineconfig.utils.options import check_tool_exists
from machineconfig.utils.io import read_json
from machineconfig.utils.schemas.installer.installer_types import InstallerData, InstallerDataFiles, get_os_name, get_normalized_arch

import platform
import subprocess
from typing import Optional
from pathlib import Path


class Installer:
    def __init__(self, installer_data: InstallerData):
        self.installer_data: InstallerData = installer_data

    def __repr__(self) -> str:
        app_name = self.installer_data["appName"]
        repo_url = self.installer_data["repoURL"]
        return f"Installer of {app_name} @ {repo_url}"

    def get_description(self) -> str:
        exe_name = self._get_exe_name()
        
        old_version_cli: bool = check_tool_exists(tool_name=exe_name)
        old_version_cli_str = "✅" if old_version_cli else "❌"
        doc = self.installer_data["doc"]
        return f"{exe_name:<12} {old_version_cli_str} {doc}"
    
    def _get_exe_name(self) -> str:
        """Derive executable name from app name by converting to lowercase and removing spaces."""
        return self.installer_data["appName"].lower().replace(" ", "").replace("-", "")

    @staticmethod
    def choose_app_and_install():
        print(f"\n{'=' * 80}\n🔍 SELECT APPLICATION TO INSTALL 🔍\n{'=' * 80}")
        from machineconfig.utils.options import choose_from_options

        print("📂 Searching for configuration files...")
        jobs_dir = Path(LIBRARY_ROOT.joinpath("jobs"))
        config_paths = [Path(p) for p in jobs_dir.rglob("config.json")]
        path = choose_from_options(multi=False, options=config_paths, msg="Choose one option")
        print(f"📄 Loading configuration from: {path}")
        config_data = read_json(path)
        installer_data_files = InstallerDataFiles(config_data)

        # Extract app names from the installers
        app_names = [installer["appName"] for installer in installer_data_files["installers"]]
        print("🔍 Select an application to install:")
        app_name = choose_from_options(multi=False, options=app_names, fzf=True, msg="Choose one option")

        # Find the selected installer data
        selected_installer_data = None
        for installer_data in installer_data_files["installers"]:
            if installer_data["appName"] == app_name:
                selected_installer_data = installer_data
                break

        if selected_installer_data is None:
            raise ValueError(f"Could not find installer data for {app_name}")

        installer = Installer(installer_data=selected_installer_data)
        exe_name = installer._get_exe_name()
        print(f"📦 Selected application: {exe_name}")
        version = input(f"📝 Enter version to install for {exe_name} [latest]: ") or None
        print(f"\n{'=' * 80}\n🚀 INSTALLING {exe_name.upper()} 🚀\n{'=' * 80}")
        installer.install(version=version)

    def install_robust(self, version: Optional[str]) -> str:
        try:
            exe_name = self._get_exe_name()
            print(f"\n{'=' * 80}\n🚀 INSTALLING {exe_name.upper()} 🚀\n{'=' * 80}")
            result_old = subprocess.run(f"{exe_name} --version", shell=True, capture_output=True, text=True)
            old_version_cli = result_old.stdout.strip()
            print(f"📊 Current version: {old_version_cli or 'Not installed'}")

            self.install(version=version)

            result_new = subprocess.run(f"{exe_name} --version", shell=True, capture_output=True, text=True)
            new_version_cli = result_new.stdout.strip()
            print(f"📊 New version: {new_version_cli}")

            if old_version_cli == new_version_cli:
                print(f"ℹ️  Same version detected: {old_version_cli}")
                return f"""📦️ 😑 {exe_name}, same version: {old_version_cli}"""
            else:
                print(f"🚀 Update successful: {old_version_cli} ➡️ {new_version_cli}")
                return f"""📦️ 🤩 {exe_name} updated from {old_version_cli} ➡️ TO ➡️  {new_version_cli}"""

        except Exception as ex:
            exe_name = self._get_exe_name()
            app_name = self.installer_data["appName"]
            print(f"❌ ERROR: Installation failed for {exe_name}: {ex}")
            return f"""📦️ ❌ Failed to install `{app_name}` with error: {ex}"""

    def install(self, version: Optional[str]) -> None:
        exe_name = self._get_exe_name()
        repo_url = self.installer_data["repoURL"]

        print(f"\n{'=' * 80}\n🔧 INSTALLATION PROCESS: {exe_name} 🔧\n{'=' * 80}")
        if repo_url == "CUSTOM":
            pass
            # import runpy
            # program: str = runpy.run_path(str(installer_path), run_name=None)["main"](version=version)
            # # print(program)
            # print("🚀 Running installation script...")
            # if platform.system() == "Linux":
            #     script = "#!/bin/bash" + "\n" + program
            # else:
            #     script = program
            # script_file = PathExtended.tmpfile(name="tmp_shell_script", suffix=".ps1" if platform.system() == "Windows" else ".sh", folder="tmp_scripts")
            # script_file.write_text(script, newline=None if platform.system() == "Windows" else "\n")
            # if platform.system() == "Windows":
            #     start_cmd = "powershell"
            #     full_command = f"{start_cmd} {script_file}"
            # else:
            #     start_cmd = "bash"
            #     full_command = f"{start_cmd} {script_file}"
            # subprocess.run(full_command, stdin=None, stdout=None, stderr=None, shell=True, text=True)
            # version_to_be_installed = str(version)
            # print(f"✅ Custom installation completed\n{'=' * 80}")

        elif "npm " in repo_url or "pip " in repo_url or "winget " in repo_url:
            package_manager = repo_url.split(" ", maxsplit=1)[0]
            print(f"📦 Using package manager: {package_manager}")
            desc = package_manager + " installation"
            version_to_be_installed = package_manager + "Latest"
            print(f"🚀 Running: {repo_url}")
            result = subprocess.run(repo_url, shell=True, capture_output=True, text=True)
            success = result.returncode == 0 and result.stderr == ""
            if not success:
                print(f"❌ {desc} failed")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                print(f"Return code: {result.returncode}")
            print(f"✅ Package manager installation completed\n{'=' * 80}")

        else:
            print("📥 Downloading from repository...")
            downloaded, version_to_be_installed = self.download(version=version)
            if str(downloaded).endswith(".deb"):
                print(f"📦 Installing .deb package: {downloaded}")
                assert platform.system() == "Linux"
                result = subprocess.run(f"sudo nala install -y {downloaded}", shell=True, capture_output=True, text=True)
                success = result.returncode == 0 and result.stderr == ""
                if not success:
                    desc = "Installing .deb"
                    print(f"❌ {desc} failed")
                    if result.stdout:
                        print(f"STDOUT: {result.stdout}")
                    if result.stderr:
                        print(f"STDERR: {result.stderr}")
                    print(f"Return code: {result.returncode}")
                print("🗑️  Cleaning up .deb package...")
                downloaded.delete(sure=True)
                print(f"✅ DEB package installation completed\n{'=' * 80}")
            else:
                if platform.system() == "Windows":
                    print("🪟 Installing on Windows...")
                    exe = find_move_delete_windows(downloaded_file_path=downloaded, exe_name=exe_name, delete=True, rename_to=exe_name.replace(".exe", "") + ".exe")
                elif platform.system() in ["Linux", "Darwin"]:
                    system_name = "Linux" if platform.system() == "Linux" else "macOS"
                    print(f"🐧 Installing on {system_name}...")
                    exe = find_move_delete_linux(downloaded=downloaded, tool_name=exe_name, delete=True, rename_to=exe_name)
                else:
                    error_msg = f"❌ ERROR: System {platform.system()} not supported"
                    print(error_msg)
                    raise NotImplementedError(error_msg)

                _ = exe
                if exe.name.replace(".exe", "") != exe_name.replace(".exe", ""):
                    from rich import print as pprint
                    from rich.panel import Panel

                    print("⚠️  Warning: Executable name mismatch")
                    pprint(Panel(f"Expected exe name: [red]{exe_name}[/red] \nAttained name: [red]{exe.name.replace('.exe', '')}[/red]", title="exe name mismatch", subtitle=repo_url))
                    new_exe_name = exe_name + ".exe" if platform.system() == "Windows" else exe_name
                    print(f"🔄 Renaming to correct name: {new_exe_name}")
                    exe.with_name(name=new_exe_name, inplace=True, overwrite=True)

        print(f"💾 Saving version information to: {INSTALL_VERSION_ROOT.joinpath(exe_name)}")
        INSTALL_VERSION_ROOT.joinpath(exe_name).parent.mkdir(parents=True, exist_ok=True)
        INSTALL_VERSION_ROOT.joinpath(exe_name).write_text(version_to_be_installed, encoding="utf-8")
        print(f"✅ Installation completed successfully!\n{'=' * 80}")

    def download(self, version: Optional[str]) -> tuple[PathExtended, str]:
        exe_name = self._get_exe_name()
        repo_url = self.installer_data["repoURL"]
        app_name = self.installer_data["appName"]
        print(f"\n{'=' * 80}\n📥 DOWNLOADING: {exe_name} 📥\n{'=' * 80}")
        
        download_link: Optional[str] = None
        version_to_be_installed: Optional[str] = None
        
        if "github" not in repo_url or ".zip" in repo_url or ".tar.gz" in repo_url:
            # Direct download URL
            download_link = repo_url
            version_to_be_installed = "predefined_url"
            print(f"🔗 Using direct download URL: {download_link}")
            print(f"📦 Version to be installed: {version_to_be_installed}")
        else:
            # GitHub repository
            print("🌐 Retrieving release information from GitHub...")
            arch = get_normalized_arch()
            os_name = get_os_name()
            
            download_link = get_github_download_link(
                repo_url=repo_url, 
                arch=arch, 
                os=os_name, 
                version=version
            )
            
            if download_link is None:
                raise ValueError(f"Could not find suitable download for {app_name} on {os_name} {arch}")
            
            # Extract version from GitHub API if possible
            if version:
                version_to_be_installed = version
            else:
                version_to_be_installed = "latest"
            
            print(f"🧭 Detected system={os_name} arch={arch}")
            print(f"� Version to be installed: {version_to_be_installed}")
            print(f"� Download URL: {download_link}")

        assert download_link is not None, "download_link must be set"
        assert version_to_be_installed is not None, "version_to_be_installed must be set"
        print(f"📥 Downloading {app_name} from: {download_link}")
        downloaded = PathExtended(download_link).download(folder=INSTALL_TMP_DIR).decompress()
        print(f"✅ Download and extraction completed to: {downloaded}\n{'=' * 80}")
        return downloaded, version_to_be_installed

    # --------------------------- Arch / template helpers ---------------------------

    @staticmethod
    def check_if_installed_already(exe_name: str, version: str, use_cache: bool) -> tuple[str, str, str]:
        print(f"\n{'=' * 80}\n🔍 CHECKING INSTALLATION STATUS: {exe_name} 🔍\n{'=' * 80}")
        version_to_be_installed = version
        INSTALL_VERSION_ROOT.joinpath(exe_name).parent.mkdir(parents=True, exist_ok=True)
        tmp_path = INSTALL_VERSION_ROOT.joinpath(exe_name)

        if use_cache:
            print("🗂️  Using cached version information...")
            if tmp_path.exists():
                existing_version = tmp_path.read_text(encoding="utf-8").rstrip()
                print(f"📄 Found cached version: {existing_version}")
            else:
                existing_version = None
                print("ℹ️  No cached version information found")
        else:
            print("🔍 Checking installed version directly...")
            result = subprocess.run([exe_name, "--version"], check=False, capture_output=True, text=True)
            if result.stdout.strip() == "":
                existing_version = None
                print("ℹ️  Could not detect installed version")
            else:
                existing_version = result.stdout.strip()
                print(f"📄 Detected installed version: {existing_version}")

        if existing_version is not None:
            if existing_version == version_to_be_installed:
                print(f"✅ {exe_name} is up to date (version {version_to_be_installed})")
                print(f"📂 Version information stored at: {INSTALL_VERSION_ROOT}")
                return ("✅ Up to date", version.strip(), version_to_be_installed.strip())
            else:
                print(f"🔄 {exe_name} needs update: {existing_version.rstrip()} → {version_to_be_installed}")
                tmp_path.write_text(version_to_be_installed, encoding="utf-8")
                return ("❌ Outdated", existing_version.strip(), version_to_be_installed.strip())
        else:
            print(f"📦 {exe_name} is not installed. Will install version: {version_to_be_installed}")
            tmp_path.write_text(version_to_be_installed, encoding="utf-8")

        print(f"{'=' * 80}")
        return ("⚠️ NotInstalled", "None", version_to_be_installed.strip())
