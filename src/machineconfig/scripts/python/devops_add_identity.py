"""ID
"""


# from platform import system
from crocodile.file_management import P as PathExtended
from machineconfig.utils.options import display_options
from rich.panel import Panel
from rich.text import Text

BOX_WIDTH = 150  # width for box drawing


def main():
    title = "🔑 SSH IDENTITY MANAGEMENT"
    print(Panel(Text(title, justify="center"), expand=False))

    print(Panel("🔍 Searching for existing SSH keys...", expand=False))

    private_keys = P.home().joinpath(".ssh").search("*.pub").apply(lambda x: x.with_name(x.stem)).filter(lambda x: x.exists())

    if private_keys:
        print(Panel(f"✅ Found {len(private_keys)} SSH private key(s)", expand=False))
    else:
        print(Panel("⚠️  No SSH private keys found", expand=False))

    choice = display_options(msg="Path to private key to be used when ssh'ing: ", options=private_keys.apply(str).list + ["I have the path to the key file", "I want to paste the key itself"])

    if choice == "I have the path to the key file":
        print(Panel("📄 Please enter the path to your private key file", expand=False))
        path_to_key = P(input("📋 Input path here: ")).expanduser().absolute()
        print(Panel(f"📂 Using key from custom path: {path_to_key}", expand=False))

    elif choice == "I want to paste the key itself":
        print(Panel("📋 Please provide a filename and paste the private key content", expand=False))
        key_filename = input("📝 File name (default: my_pasted_key): ") or "my_pasted_key"
        path_to_key = P.home().joinpath(f".ssh/{key_filename}").write_text(input("🔑 Paste the private key here: "))
        print(Panel(f"💾 Key saved to: {path_to_key}", expand=False))

    elif isinstance(choice, str):
        path_to_key = P(choice)
        print(Panel(f"🔑 Using selected key: {path_to_key.name}", expand=False))

    else:
        error_message = f"❌ ERROR: Invalid choice\nThe selected option is not supported: {choice}"
        print(Panel(Text(error_message, justify="center"), expand=False, border_style="red"))
        raise NotImplementedError(f"Choice {choice} not supported")

    txt = f"IdentityFile {path_to_key.collapseuser().as_posix()}"  # adds this id for all connections, no host specified.
    config_path = P.home().joinpath(".ssh/config")

    print(Panel("📝 Updating SSH configuration...", expand=False))

    if config_path.exists():
        config_path.modify_text(txt_search=txt, txt_alt=txt, replace_line=True, notfound_append=True, prepend=True)  # note that Identity line must come on top of config file otherwise it won't work, hence `prepend=True`
        print(Panel("✏️  Updated existing SSH config file", expand=False))
    else:
        config_path.write_text(txt)
        print(Panel("📄 Created new SSH config file", expand=False))

    panel_complete = Panel(
        Text(
            "✅ SSH IDENTITY CONFIGURATION COMPLETE\n"
            "Identity added to SSH config file\n"
            "Consider reloading the SSH config to apply changes",
            justify="center"
        ),
        expand=False,
        border_style="green"
    )
    program = f"echo '{panel_complete}'"

    success_message = f"🎉 CONFIGURATION SUCCESSFUL\nIdentity added: {path_to_key.name}\nConfig file: {config_path}"
    print(Panel(Text(success_message, justify="center"), expand=False, border_style="green"))

    return program


if __name__ == '__main__':
    pass
