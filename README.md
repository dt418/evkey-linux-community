# EVKey Linux Community

Bộ gõ tiếng Việt cho Fcitx5 trên Linux, dựa trên mã nguồn Fcitx5 Lotus và Bamboo. Đây là dự án cộng đồng độc lập.

**Bản cộng đồng lấy cảm hứng từ EVKey; sử dụng Lotus/Bamboo, không phải bản EVKey chính thức.** Không liên kết, xác nhận hoặc phân phối bởi tác giả EVKey.

## Chế độ

- **Preedit** — hiển thị phần đang gõ trước khi commit; không cần helper đặc quyền.
- **Fake Backspace** — thay thế ký tự bằng sự kiện backspace ứng dụng; không cần helper đặc quyền.
- **Uinput (Smooth)** — chế độ tùy chọn qua gói `fcitx5-evkey-uinput`. Helper bị từ chối hoặc không sẵn sàng sẽ quay về Preedit. Helper không đọc thiết bị bàn phím.

Mã nguồn engine kế thừa hỗ trợ `Telex`, `VNI`, `Telex + VNI`, `Telex + VNI + VIQR`, `VIQR`, `Microsoft layout`, `VNI Bàn phím tiếng Pháp`, và `Custom`. `VIQR` nhận cả `+` lẫn `*` để gõ `ư/ơ`, tương thích thao tác VIQR* của X-Unikey nên không cần lựa chọn trùng riêng. Bảng mã gồm Unicode, TCVN3 (ABC), VNI Windows, Unicode tổ hợp, Windows 1258, VIQR, VISCII, VPS, BKHCM 1/2, Vietware X/Full, UTF-8, NCR Decimal/Hex, và Unicode C string Hex/Decimal. Settings hiển thị đầy đủ các lựa chọn backend cung cấp.

## Khay hệ thống và chuyển nhanh

Menu trạng thái của EVKey trong Fcitx5 có mục **Settings**, **Input Method**, và **Charset**. Mở **Input Method** để chọn Telex/VNI/VIQR hoặc kiểu kết hợp; **Charset** để chọn bảng mã. Các lựa chọn được lưu vào cấu hình Fcitx5. Cửa sổ Settings cũng có combobox tương ứng.

## Build

Debian/Ubuntu dependencies:

```sh
sudo apt install cmake extra-cmake-modules g++ golang pkg-config \
  fcitx5-modules-dev libfcitx5core-dev libfcitx5config-dev \
  libfcitx5utils-dev libinput-dev libudev-dev libsystemd-dev gettext \
  python3-qtpy python3-dbus acl librsvg2-bin
```

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Install packages separately by component:

```sh
sudo cmake --install build --component Runtime
sudo cmake --install build --component Uinput  # optional privileged helper
```

Other distro package recipes are under `packaging/`. Arch recipe expects release archive and SHA-256 supplied through its documented makepkg variables; it does not download unverified source.

### NixOS

`flake.nix` xuất package `packages.<system>.default` và module `nixosModules.default`. Thêm module vào cấu hình NixOS rồi đặt `programs.fcitx5-evkey.enable = true;`. Gói chính chỉ cài runtime. `programs.fcitx5-evkey.uinput.enable = true;` cài helper tùy chọn, account, systemd unit, kernel module và udev rules; module không tự khởi chạy service. Chỉ chạy `fcitx5-evkey-server@<UID>.service` khi phiên desktop của UID đó đang hoạt động.

## Security boundary

Runtime component and distro main packages omit helper executable, account, udev rules, and service. CMake install without `--component` installs all components; use Runtime-only if Smooth is not needed. Installing Uinput does not enable its service. Optional helper runs as dedicated `evkey-input` account. It checks Unix peer credentials, active unlocked logind session, caller UID, and protocol framing; it does not read keyboard devices or inspect `/proc` command lines. Udev grants helper access only to `/dev/uinput` and eligible non-keyboard pointing devices. Review local distro/systemd/udev policy before enabling it.

## License and attribution

Project distributed under GPL-3.0-or-later; see `LICENSE`. Imported Fcitx5 Lotus and Bamboo sources retain upstream copyright and notices. `bamboo/bamboo-core` carries its own license. Do not remove attribution when redistributing.
