Name:           fcitx5-evkey
Version:        1.0.0
Release:        4%{?dist}
Summary:        Vietnamese input method for Fcitx 5
License:        GPL-3.0-or-later
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  cmake >= 3.16
BuildRequires:  extra-cmake-modules
BuildRequires:  gcc-c++
BuildRequires:  gettext-devel
BuildRequires:  fcitx5-devel >= 5.1.7
BuildRequires:  libinput-devel
BuildRequires:  pkgconfig(libudev)
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  golang
BuildRequires:  python3-devel
BuildRequires:  python3-QtPy
BuildRequires:  python3-dbus
BuildRequires:  (python3-pyqt6 or python3-pyside6)
BuildRequires:  librsvg2-tools

Requires:       fcitx5 >= 5.1.7
Requires:       python3-QtPy
Requires:       (python3-pyqt6 or python3-pyside6)
Requires:       python3-dbus

%description
EVKey Linux Community is a Vietnamese input method for Fcitx 5. It is
community software inspired by EVKey, using Lotus/Bamboo; it is not an
official EVKey release. Preedit and Fake Backspace require no privileged
helper.

%package uinput
Summary:        Optional uinput helper for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       acl
Requires:       systemd
Requires:       udev

%description uinput
Optional helper for EVKey Linux Community Smooth mode. It runs as dedicated
system account evkey-input and can inject keys into an active local desktop
session. It is never enabled automatically.

%prep
%autosetup -n %{name}-%{version}

%build
%cmake -DEVKEY_BYTECOMPILE_PYTHON:BOOL=OFF -DBUILD_TESTING:BOOL=ON
%cmake_build

%install
%cmake_install
%find_lang %{name}
%py_byte_compile %{__python3} %{buildroot}%{_datadir}/fcitx5-evkey

%pre uinput
/usr/bin/systemd-sysusers %{_sysusersdir}/evkey-input.conf >/dev/null 2>&1 || :

%post uinput
%systemd_post fcitx5-evkey-server@.service
/usr/bin/udevadm control --reload-rules >/dev/null 2>&1 || :
/usr/bin/udevadm trigger --subsystem-match=misc --sysname-match=uinput >/dev/null 2>&1 || :
/usr/bin/udevadm trigger --subsystem-match=input --sysname-match=event* >/dev/null 2>&1 || :

echo "Smooth mode can inject keys into this desktop session. Enable only when needed:"
echo "  sudo systemctl enable --now fcitx5-evkey-server@\$(id -u).service"

%preun uinput
if [ "$1" -eq 0 ]; then
    /usr/bin/systemctl stop 'fcitx5-evkey-server@*.service' >/dev/null 2>&1 || :
    for node in /dev/uinput /dev/input/event*; do
        [ -e "$node" ] || continue
        /usr/bin/setfacl -x u:evkey-input "$node" >/dev/null 2>&1 || :
    done
fi
%systemd_preun fcitx5-evkey-server@.service

%postun uinput
%systemd_postun fcitx5-evkey-server@.service
/usr/bin/udevadm control --reload-rules >/dev/null 2>&1 || :

%check
%ctest

%files -f %{name}.lang
%license LICENSE
%{_bindir}/fcitx5-evkey-settings
%{_libdir}/fcitx5/libevkey.so
%{_datadir}/fcitx5/addon/evkey.conf
%{_datadir}/fcitx5/inputmethod/evkey.conf
%{_datadir}/fcitx5/evkey/
%{_datadir}/fcitx5-evkey/
%{_datadir}/applications/org.fcitx.Fcitx5.Addon.Evkey.Settings.desktop
%{_datadir}/metainfo/org.fcitx.Fcitx5.Addon.Evkey.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/fcitx-evkey*.svg
%{_datadir}/icons/hicolor/scalable/status/fcitx-evkey*.svg
%{_datadir}/icons/hicolor/*/status/fcitx-evkey*.png

%files uinput
%{_bindir}/fcitx5-evkey-server
%{_modulesloaddir}/fcitx5-evkey.conf
%{_unitdir}/fcitx5-evkey-server@.service
%{_sysusersdir}/evkey-input.conf
%{_udevrulesdir}/99-evkey-uinput.rules

%changelog
* Mon Oct 05 2026 EVKey Linux Community <me@danhthanh.dev> - 1.0.0-4
- Keep dynamic Settings scrollbars vertical during Fcitx recovery.

* Sun Oct 04 2026 EVKey Linux Community <me@danhthanh.dev> - 1.0.0-3
- Restore Settings tab scrolling after Fcitx recovery.

* Sun Oct 04 2026 EVKey Linux Community <me@danhthanh.dev> - 1.0.0-2
- Hide stale Settings configuration errors after Fcitx recovery.

* Sun Oct 04 2026 EVKey Linux Community <me@danhthanh.dev> - 1.0.0-1
- Initial EVKey Linux Community package split
