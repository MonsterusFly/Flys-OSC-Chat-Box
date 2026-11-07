# Update system — enhanced v1.3.0 test build

This source preview adds a Settings > Software updates panel.

- Check GitHub's **latest public stable release** at startup (optional), or with the manual check button.
- Display available version, Fedora RPM filename, download size, and plain-text release notes.
- Optionally **download** a compatible Fedora RPM automatically after a successful check.
- Downloaded RPMs are verified using the `.rpm.sha256` sidecar published by the GitHub Actions RPM workflow.
- **Installation is never automatic.** You must select Install verified update and approve Fedora's administrator prompt.
- Install is available **only when this running application was installed using the Fedora RPM**. Preview/source instances cannot install upgrades.
- Quit and relaunch the application after installing. All settings remain under `~/.config/linux-osc-chatbox`.

## Private repositories

GitHub's public `/releases/latest` API returns HTTP 404 for private repositories, even if a release exists. This updater explains the error, but does not request, store, or embed a personal access token. To enable public in-app update checks, publish the repository and stable releases when ready. Until then, install releases manually from GitHub while logged into your account. **Do not make the repository public without reviewing its contents and secrets first.**

## Security notes

GitHub-hosted RPM and SHA-256 sidecar validate transfer integrity but do not provide independent proof of publisher identity. Use trusted tags, keep GitHub account secure, and review unexpected update prompts. Downloads/installations require network access. The application never silently requests administrator privileges.

## Testing

```bash
python3 -m pytest -q
python3 main.py
```

Test UI from source first. Verify real RPM installation and Polkit authorization on your Fedora machine before tagging a release.
