/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành <thanhpy2009@gmail.com>
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ  <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

#ifndef _LOTUS_SERVER_H_
#define _LOTUS_SERVER_H_

#include <atomic>
#include <cstdint>
#include <fcntl.h>
#include <libinput.h>
#include <linux/uinput.h>
#include <string>
#include <sys/socket.h>
#include <sys/un.h>

class FdGuard {
  public:
    explicit FdGuard(int fd = -1) : fd_(fd) {}
    ~FdGuard();

    FdGuard(const FdGuard&) = delete;
    FdGuard& operator=(const FdGuard&) = delete;
    FdGuard(FdGuard&& other) noexcept;
    FdGuard& operator=(FdGuard&& other) noexcept;

    int get() const {
        return fd_;
    }
    bool is_valid() const {
        return fd_ >= 0;
    }
    void reset(int new_fd = -1);

  private:
    int fd_;
};

class UinputDevice {
  public:
    UinputDevice() = default;
    ~UinputDevice();

    UinputDevice(const UinputDevice&) = delete;
    UinputDevice& operator=(const UinputDevice&) = delete;
    UinputDevice(UinputDevice&&) = default;
    UinputDevice& operator=(UinputDevice&&) = default;

    bool initialize();
    void reset();
    bool send_backspace();
    bool send_delete();
    bool send_shift_down();
    bool send_shift_up();
    bool send_left();
    int get_fd() const {
        return guard_.get();
    }

  private:
    bool send_tap(std::uint16_t code);
    bool send_mod(std::uint16_t code, int value);

    FdGuard guard_;
};

class LibinputContext {
  public:
    LibinputContext(const struct libinput_interface* interface);
    ~LibinputContext();

    LibinputContext(const LibinputContext&) = delete;
    LibinputContext& operator=(const LibinputContext&) = delete;
    LibinputContext(LibinputContext&&) = delete;
    LibinputContext& operator=(LibinputContext&&) = delete;

    bool is_valid() const {
        return li_ != nullptr;
    }
    struct libinput* get_li() const {
        return li_;
    }
    int get_fd() const;
    struct udev* get_udev() const {
        return udev_;
    }

  private:
    struct udev* udev_ = nullptr;
    struct libinput* li_ = nullptr;
};

#define UNIX_PATH_MAX sizeof(((struct sockaddr_un*)0)->sun_path)

extern std::atomic<bool> g_running;

void signal_handler(int sig);
int open_restricted(const char* path, int flags, void* user_data);
void close_restricted(int fd, void* user_data);
extern const struct libinput_interface interface;

int main(int argc, char* argv[]);

#endif // _LOTUS_SERVER_H_
