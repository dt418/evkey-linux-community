# Đóng góp

EVKey Linux Community là dự án cộng đồng độc lập dựa trên mã nguồn Fcitx5 Lotus và Bamboo. Giữ nguyên giấy phép, bản quyền và ghi nhận upstream khi sửa hoặc phân phối mã nguồn.

**Bản cộng đồng lấy cảm hứng từ EVKey; sử dụng Lotus/Bamboo, không phải bản EVKey chính thức.**

## Build và kiểm thử

Xem dependencies và lệnh build tại [README.md](README.md). Dùng build directory riêng:

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Thay đổi engine/helper cần kiểm thử trong phiên Fcitx5 Linux thật. Test unit/build không thay thế kiểm tra nhập liệu trực tiếp. Không gửi thay đổi mở rộng quyền helper hoặc cấp quyền đọc thiết bị bàn phím nếu không có thiết kế bảo mật được duyệt.

## Thay đổi

- Giữ phạm vi nhỏ và tương thích với CMake 3.16, C++17, Go 1.18.
- Cập nhật tài liệu và kiểm thử hành vi có thể quan sát khi hợp đồng thay đổi.
- Không đưa token, dữ liệu gõ, hay thông tin nhận dạng người dùng vào log.
- Không thêm workflow phát hành, ký gói, hoặc tự động xuất bản artifact.
- Nêu rõ môi trường và lệnh đã chạy trong pull request; không khẳng định kiểm thử desktop nếu chưa chạy.

## Báo lỗi

Kèm distro/phiên bản, phiên bản Fcitx5, chế độ bộ gõ, bước tái hiện và log đã loại dữ liệu nhạy cảm. Không gửi nội dung văn bản đã gõ hoặc thông tin cá nhân.
