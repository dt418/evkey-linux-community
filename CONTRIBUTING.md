# Đóng góp

EVKey Linux Community là dự án cộng đồng độc lập dựa trên mã nguồn Fcitx5 Lotus và Bamboo. Giữ nguyên giấy phép, bản quyền và ghi nhận upstream khi sửa hoặc phân phối mã nguồn.

**Bản cộng đồng lấy cảm hứng từ EVKey; sử dụng Lotus/Bamboo, không phải bản EVKey chính thức.**

## Build và kiểm thử

Tham khảo dependencies tại [README.md](README.md); các bước CMake, Go, Settings và D-Bus có chung harness trong [docs/development.md](docs/development.md):

```sh
tools/dev.sh help
tools/dev.sh check
tools/dev.sh settings
tools/dev.sh dbus
```

Thay đổi engine/helper cần kiểm thử trong phiên Fcitx5 Linux thật. Test unit/build không thay thế kiểm tra nhập liệu trực tiếp. Không gửi thay đổi mở rộng quyền helper hoặc cấp quyền đọc thiết bị bàn phím nếu không có thiết kế bảo mật được duyệt.

## Thay đổi

- Giữ phạm vi nhỏ và tương thích với CMake 3.16, C++17, Go 1.18.
- Dùng test-driven development cho thay đổi hành vi: chứng minh test seam hiện có thất bại vì lỗi mục tiêu, sửa tối thiểu, chạy lại test rồi smoke bề mặt thật. Tài liệu và test mock không chứng minh tương thích desktop/hardware.
- Skill Superpowers và ba skill chuyên biệt cho engine, Settings, packaging nằm trong `.agents/skills/`; pin upstream theo `skills-lock.json`.
- Không thêm release, package-signing hoặc artifact-publishing workflow tự động.
- Nêu rõ môi trường và lệnh đã chạy trong pull request; không khẳng định kiểm thử desktop nếu chưa chạy.

## Báo lỗi

Kèm distro/phiên bản, phiên bản Fcitx5, chế độ bộ gõ, bước tái hiện và log đã loại dữ liệu nhạy cảm. Không gửi nội dung văn bản đã gõ hoặc thông tin cá nhân.
