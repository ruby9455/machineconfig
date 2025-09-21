"""Mount a remote SSHFS share on a local directory"""

from platform import system
from machineconfig.utils.ssh import SSH
from machineconfig.utils.terminal import Terminal
from machineconfig.utils.path_reduced import PathExtended as PathExtended
from machineconfig.utils.source_of_truth import PROGRAM_PATH
from machineconfig.utils.options import choose_ssh_host


def main():
    print("\n" + "=" * 50)
    print("🚀 Starting SSHFS Mounting Process")
    print("=" * 50 + "\n")

    share_info = input("🔗 Enter share path (e.g., user@host:/path) [Press Enter for interactive choice]: ")
    if share_info == "":
        print("\n🔍 Interactive mode selected for choosing share path.")
        tmp = choose_ssh_host(multi=False)
        assert isinstance(tmp, str)
        ssh = SSH(host=tmp)
        share_info = f"{ssh.username}@{ssh.hostname}:{ssh.run('echo $HOME').op}/data/share_ssh"
    else:
        ssh = SSH(share_info.split(":")[0])

    print(f"\n🌐 Share Info: {share_info}")

    if system() == "Windows":
        print("\n🔍 Checking existing drives...")
        print(Terminal().run("net use", shell="powershell").op)
        driver_letter = input(r"🖥️ Choose driver letter (e.g., Z:\\) [Avoid already used ones]: ") or "Z:\\"
    else:
        driver_letter = None

    mount_point = input(f"📂 Enter the mount point directory (e.g., /mnt/network) [Default: ~/data/mount_ssh/{ssh.hostname}]: ")
    if mount_point == "":
        mount_point = PathExtended.home().joinpath(rf"data/mount_ssh/{ssh.hostname}")

    print(f"\n📁 Mount Point: {mount_point}")

    if system() == "Linux":
        txt = """
sshfs alex@:/media/dbhdd /media/dbhdd\
"""
        print("\n🔧 Preparing SSHFS mount command for Linux...")
    elif system() == "Windows":
        txt = rf"""
net use {driver_letter} {share_info}
fusermount -u /mnt/dbhdd
"""
        print("\n🔧 Preparing SSHFS mount command for Windows...")
    else:
        raise ValueError(f"❌ Not implemented for this system: {system()}")

    PROGRAM_PATH.write_text(txt, encoding="utf-8")
    print("✅ Configuration saved successfully!\n")

    print("🎉 SSHFS Mounting Process Completed!\n")


if __name__ == "__main__":
    main()
