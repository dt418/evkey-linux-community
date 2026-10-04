# EVKey chính thức: kiểu gõ và bảng mã

**Phạm vi.** Báo cáo chỉ dùng nguồn first-party EVKey: trang chủ và repository/release của tác giả. “Bảng mã” là nhãn EVKey; báo cáo không tự quy đổi mọi lựa chọn thành encoding chuẩn Unicode.

## Kết luận

**Có.** EVKey chính thức cho chọn cả **kiểu gõ** lẫn **bảng mã**. Trang chủ liệt kê Telex, VNI, VIQR và “các kiểu gõ kết hợp”; Unicode, TCVN3 (ABC), VNI Windows, Unicode tổ hợp, cùng “nhiều bảng mã khác”. [Trang chủ EVKey — “Hỗ trợ đầy đủ các kiểu gõ và bảng mã”](https://evkeyvn.com/)

Danh sách trên không phải danh sách đầy đủ có thể kiểm chứng từ nguồn đã xem: cụm “nhiều bảng mã khác” không nêu tên từng bảng mã. Không được coi đây là chứng cứ mọi tùy chọn của từng bản phát hành hay từng hệ điều hành.

## Tùy chọn xác nhận được

| Nhóm | Nhãn/giá trị chính thức xác nhận được | Ý nghĩa và bằng chứng |
|---|---|---|
| Kiểu gõ | `Telex`, `VNI`, `VIQR`, `các kiểu gõ kết hợp` | Trang chủ liệt kê các kiểu gõ này. [Nguồn](https://evkeyvn.com/) |
| Bảng mã | `Unicode`, `TCVN3 (ABC)`, `VNI Windows`, `Unicode tổ hợp`, `nhiều bảng mã khác` | Trang chủ liệt kê nguyên văn các nhãn này. “Unicode tổ hợp” giữ nguyên nhãn nguồn; nguồn không định nghĩa chi tiết mapping. [Nguồn](https://evkeyvn.com/) |
| Giá trị đang chọn trong UI Windows minh họa | Bảng mã `Unicode`; kiểu gõ `Telex` | Ảnh giao diện chính thức hiển thị hai combobox **Bảng mã** và **Kiểu gõ** với các giá trị đó. Đây là bằng chứng các giá trị hiện diện, không chứng minh toàn bộ nội dung menu. [Ảnh 1](https://raw.githubusercontent.com/lamquangminh/EVKey/master/docs/evkey-screenshot-1.png), [ảnh 2](https://raw.githubusercontent.com/lamquangminh/EVKey/master/docs/evkey-screenshot-2.png) |
| Chế độ nhập Windows | `Keyboard hook`, `IME` | Trang chủ nói rõ: **trên Windows** người dùng có thể chọn giữa hai cơ chế này. Cùng hai nhãn radio xuất hiện trong ảnh UI chính thức. [Trang chủ](https://evkeyvn.com/), [ảnh UI](https://raw.githubusercontent.com/lamquangminh/EVKey/master/docs/evkey-screenshot-1.png) |
| Chuyển Việt/Anh | Phím tắt, nhãn phím không nêu | EVKey nói có thể chuyển nhanh giữa gõ tiếng Việt và tiếng Anh bằng phím tắt, nhưng nguồn đã xem không nêu tổ hợp cụ thể. [Nguồn](https://evkeyvn.com/) |

## Cách kích hoạt/chuyển lựa chọn

- **Windows:** chạy EVKey, sau đó nhấp phải biểu tượng EVKey ở system tray để chọn **kiểu gõ** — hướng dẫn nêu ví dụ `Telex/VNI` — và **bảng mã** — nêu ví dụ `Unicode`. [Hướng dẫn Windows, bước 3–5](https://evkeyvn.com/)
- **macOS:** chọn kiểu gõ và bảng mã từ biểu tượng EVKey trên menu bar; trước đó EVKey yêu cầu quyền Accessibility để bộ gõ hoạt động. [Hướng dẫn macOS, bước 3–4](https://evkeyvn.com/)
- **Chỉ Windows, khi nguồn nói rõ:** chọn `Keyboard hook` hoặc `IME` để tương thích/ổn định theo máy hoặc ứng dụng. [Trang chủ — “Hai cơ chế gõ: Keyboard hook & IME”](https://evkeyvn.com/)

## Phạm vi nền tảng và điều chưa xác minh

EVKey tự mô tả hỗ trợ Windows và macOS; trang chủ hiện liên kết Windows `v6.0.5` và macOS `v3.3.10`. Release chính thức cùng nêu “update Windows 6.0.5, Mac 3.3.10”. [Trang chủ](https://evkeyvn.com/), [release chính thức](https://github.com/lamquangminh/EVKey/releases/tag/Release)

Nguồn chỉ liệt kê kiểu gõ/bảng mã ở cấp sản phẩm rồi nêu cách chọn riêng trên Windows và macOS. Vì vậy, **không xác minh được** từng giá trị có mặt trên cả hai hệ điều hành, danh sách dropdown đầy đủ, shortcut Việt/Anh chính xác, hoặc macOS có cơ chế tương đương `Keyboard hook`/`IME`. Không suy diễn các điểm này thành parity bắt buộc cho EVKey Linux Community.

## Tham chiếu Linux: X-Unikey

Trang UniKey mô tả X-Unikey là bản Linux/FreeBSD, có các phương thức `TELEX`, `VNI`, `VIQR`, `VIQR*`, cùng các tập ký tự `UNICODE (UTF-8)`, `TCVN`, `VNI`, `VIQR`. Manual cho phép đổi bảng mã và kiểu gõ qua phím tắt hoặc biểu tượng giao diện; nhấp phải đổi bảng mã, `Ctrl` + nhấp phải đổi kiểu gõ. [Trang X-Unikey](https://www.unikey.org/linux.html), [manual X-Unikey, mục 2 và 4.1](https://www.unikey.org/support/x-unikey-manual.html)

EVKey Linux Community đang có lựa chọn Telex, VNI, VIQR và tổ hợp trong cấu hình/tray menu; bảng mã hiện có Unicode, TCVN3 (ABC), VNI Windows, VIQR và nhiều bảng mã khác. Không có lựa chọn menu riêng `VIQR*`, nhưng mapping VIQR của Bamboo nhận cả `*` và `+` cho modifier Ư/Ơ (`bamboo/bamboo-core/input_method_def.go`). X-Unikey source cũng ánh xạ cả hai ký tự này vào cùng `vneHook_uo` (`src/ukengine/inputproc.cpp`, [mã nguồn 1.0.4](http://prdownloads.sourceforge.net/unikey/x-unikey-1.0.4.tar.bz2)). Menu Fcitx5 cung cấp lựa chọn nhanh thay cho click-modifier riêng; EVKey Linux Community không sao chép các phím tắt X-Unikey mặc định.
