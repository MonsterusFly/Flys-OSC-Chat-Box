Name:           flys-osc-chat-box
Version:        1.3.5
Release:        1%{?dist}
Summary:        VRChat OSC chatbox and music/status companion for Linux
License:        MIT AND OFL-1.1
URL:            https://github.com/MonsterusFly/Flys-OSC-Chat-Box
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       python3-pyside6
Requires:       python3-psutil
Requires:       python3-pillow
Requires:       polkit
Recommends:     playerctl

%description
Fly's OSC Chat Box is a configurable VRChat OSC chatbox with rotating statuses,
music playback progress and system monitoring. User settings are never packaged.

%prep
# The source tree is checked out by the build workflow.

%build

%install
mkdir -p %{buildroot}%{_datadir}/flys-osc-chat-box
cp -a %{_sourcedir}/main.py %{_sourcedir}/core %{_sourcedir}/ui %{_sourcedir}/integrations %{_sourcedir}/assets %{_sourcedir}/packaging %{buildroot}%{_datadir}/flys-osc-chat-box/
find %{buildroot}%{_datadir}/flys-osc-chat-box -type d -name __pycache__ -prune -exec rm -rf {} +
find %{buildroot}%{_datadir}/flys-osc-chat-box -type f -name '*.pyc' -delete
mkdir -p %{buildroot}%{_bindir} %{buildroot}%{_datadir}/applications %{buildroot}%{_datadir}/licenses/%{name}
install -m 755 %{_sourcedir}/packaging/fedora/launch.sh %{buildroot}%{_bindir}/flys-osc-chat-box
install -m 644 %{_sourcedir}/packaging/fedora/flys-osc-chat-box.desktop %{buildroot}%{_datadir}/applications/
install -m 644 %{_sourcedir}/packaging/fedora/flys-osc-chat-box-uninstall.desktop %{buildroot}%{_datadir}/applications/
install -m 644 %{_sourcedir}/LICENSE %{buildroot}%{_datadir}/licenses/%{name}/LICENSE
install -m 644 %{_sourcedir}/LICENSES/OFL-1.1.txt %{buildroot}%{_datadir}/licenses/%{name}/OFL-1.1.txt
mkdir -p %{buildroot}%{_datadir}/doc/%{name}
install -m 644 %{_sourcedir}/THIRD_PARTY_NOTICES.md %{buildroot}%{_datadir}/doc/%{name}/THIRD_PARTY_NOTICES.md

%files
%{_bindir}/flys-osc-chat-box
%{_datadir}/flys-osc-chat-box/
%{_datadir}/applications/flys-osc-chat-box.desktop
%{_datadir}/applications/flys-osc-chat-box-uninstall.desktop
%{_datadir}/licenses/%{name}/LICENSE
%{_datadir}/licenses/%{name}/OFL-1.1.txt
%{_datadir}/doc/%{name}/THIRD_PARTY_NOTICES.md

%changelog
* Sat Nov 07 2026 MonsterusFly - 1.3.0-1
- Add update detection and user-authorized RPM update integration

* Sat Nov 07 2026 MonsterusFly - 1.2.0-1
- Add RPM packaging and graphical uninstall option
