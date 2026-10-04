/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành <thanhpy2009@gmail.com>
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ  <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

#include "lotus-server.h"
#include "lotus-logger.h"
#include "../src/lotus-protocol.h"

#include <array>
#include <chrono>
#include <climits>
#include <cstddef>
#include <cerrno>
#include <csignal>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <poll.h>
#include <pwd.h>
#include <set>
#include <systemd/sd-bus.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <unistd.h>

#include <libudev.h>

std::atomic<bool> g_running{true};

namespace {

constexpr char kHelperAccount[] = "evkey-input";
constexpr char kLogindService[] = "org.freedesktop.login1";
constexpr char kLogindPath[] = "/org/freedesktop/login1";
constexpr char kSessionInterface[] = "org.freedesktop.login1.Session";

bool write_all(int fd, const void* buffer, std::size_t size) {
    const auto* bytes = static_cast<const std::uint8_t*>(buffer);
    while (size > 0) {
        const ssize_t written = write(fd, bytes, size);
        if (written > 0) {
            bytes += written;
            size -= static_cast<std::size_t>(written);
            continue;
        }
        if (written < 0 && errno == EINTR)
            continue;
        return false;
    }
    return true;
}

bool property_is_one(struct udev_device* device, const char* name) {
    for (struct udev_device* current = device; current != nullptr; current = udev_device_get_parent(current)) {
        const char* value = udev_device_get_property_value(current, name);
        if (value != nullptr && strcmp(value, "1") == 0)
            return true;
    }
    return false;
}

bool is_helper_virtual_device(struct udev_device* device) {
    for (struct udev_device* current = device; current != nullptr; current = udev_device_get_parent(current)) {
        if (property_is_one(current, "ID_VIRTUAL"))
            return true;
        const char* name = udev_device_get_sysattr_value(current, "name");
        if (name != nullptr && strcmp(name, "fcitx5-evkey-server") == 0)
            return true;
    }
    return false;
}

class SessionGate {
  public:
    explicit SessionGate(uid_t target_uid) : target_uid_(target_uid) {}

    ~SessionGate() {
        if (bus_ != nullptr)
            sd_bus_unref(bus_);
    }

    bool initialize() {
        if (sd_bus_open_system(&bus_) < 0 || bus_ == nullptr)
            return false;
        if (sd_bus_set_exit_on_disconnect(bus_, 0) < 0 ||
            sd_bus_add_match(bus_, nullptr,
                             "type='signal',sender='org.freedesktop.login1',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged',path_namespace='/org/freedesktop/login1/session'",
                             signal_callback, this) < 0 ||
            sd_bus_add_match(bus_, nullptr,
                             "type='signal',sender='org.freedesktop.login1',interface='org.freedesktop.login1.Manager',member='SessionRemoved'",
                             signal_callback, this) < 0 ||
            sd_bus_add_match(bus_, nullptr,
                             "type='signal',sender='org.freedesktop.login1',interface='org.freedesktop.login1.Manager',member='PrepareForSleep'",
                             signal_callback, this) < 0) {
            sd_bus_unref(bus_);
            bus_ = nullptr;
            return false;
        }
        refresh();
        return query_ok_;
    }

    int fd() const {
        return bus_ == nullptr ? -1 : sd_bus_get_fd(bus_);
    }

    short events() const {
        return bus_ == nullptr ? 0 : static_cast<short>(sd_bus_get_events(bus_));
    }

    bool has_changed() const {
        return changed_;
    }

    bool check() {
        if (bus_ == nullptr || !process())
            return false;
        // Re-read policy for every input batch. Signals reduce stale windows; failures deny input.
        const bool active = refresh();
        return query_ok_ && active;
    }

    bool process() {
        if (bus_ == nullptr)
            return false;
        int result = 0;
        while ((result = sd_bus_process(bus_, nullptr)) > 0) {
        }
        if (result < 0)
            return false;
        return true;
    }

  private:
    static int signal_callback(sd_bus_message* message, void* userdata, sd_bus_error*) {
        auto* gate = static_cast<SessionGate*>(userdata);
        const char* member = sd_bus_message_get_member(message);
        if (member != nullptr && strcmp(member, "PrepareForSleep") == 0) {
            int sleeping = 0;
            if (sd_bus_message_read(message, "b", &sleeping) < 0)
                gate->signal_error_ = true;
            else
                gate->sleeping_ = sleeping != 0;
        }
        gate->changed_ = true;
        return 0;
    }

    bool get_bool(const char* path, const char* property, bool& value) const {
        int raw = 0;
        if (sd_bus_get_property_trivial(bus_, kLogindService, path, kSessionInterface, property, nullptr, 'b', &raw) < 0)
            return false;
        value = raw != 0;
        return true;
    }

    bool get_string(const char* path, const char* property, std::string& value) const {
        char* raw = nullptr;
        if (sd_bus_get_property_string(bus_, kLogindService, path, kSessionInterface, property, nullptr, &raw) < 0)
            return false;
        value = raw;
        free(raw);
        return true;
    }

    bool session_is_eligible(const char* path) const {
        bool active = false;
        bool remote = true;
        bool locked = true;
        std::string type;
        std::string session_class;
        std::string seat;
        return get_bool(path, "Active", active) && get_bool(path, "Remote", remote) && get_bool(path, "LockedHint", locked) &&
               get_string(path, "Type", type) && get_string(path, "Class", session_class) && get_string(path, "Seat", seat) && active &&
               !remote && !locked && seat == "seat0" && session_class == "user" && (type == "x11" || type == "wayland");
    }

    bool refresh() {
        query_ok_ = false;
        if (bus_ == nullptr || signal_error_ || sleeping_)
            return false;

        sd_bus_error error = SD_BUS_ERROR_NULL;
        sd_bus_message* reply = nullptr;
        const int call_result = sd_bus_call_method(bus_, kLogindService, kLogindPath, "org.freedesktop.login1.Manager", "ListSessions", &error,
                                                   &reply, "");
        if (call_result < 0) {
            sd_bus_error_free(&error);
            sd_bus_message_unref(reply);
            return false;
        }

        std::size_t target_sessions = 0;
        bool eligible = false;
        int result = sd_bus_message_enter_container(reply, 'a', "(susso)");
        while (result > 0) {
            const char* id = nullptr;
            const char* user = nullptr;
            const char* seat = nullptr;
            const char* path = nullptr;
            std::uint32_t uid = 0;
            result = sd_bus_message_enter_container(reply, 'r', "susso");
            if (result <= 0)
                break;
            result = sd_bus_message_read(reply, "susso", &id, &uid, &user, &seat, &path);
            const int exit_result = sd_bus_message_exit_container(reply);
            if (result < 0 || exit_result < 0)
                break;
            if (uid == target_uid_) {
                ++target_sessions;
                if (seat != nullptr && strcmp(seat, "seat0") == 0 && path != nullptr && session_is_eligible(path))
                    eligible = true;
            }
            result = sd_bus_message_at_end(reply, 0) ? 0 : 1;
        }
        const int array_exit_result = sd_bus_message_exit_container(reply);
        sd_bus_message_unref(reply);
        sd_bus_error_free(&error);
        if (result < 0 || array_exit_result < 0)
            return false;

        query_ok_ = true;
        changed_ = false;
        return target_sessions == 1 && eligible;
    }

    uid_t target_uid_;
    sd_bus* bus_ = nullptr;
    bool changed_ = false;
    bool sleeping_ = false;
    bool signal_error_ = false;
    bool query_ok_ = false;
};

bool helper_account_matches_process() {
    struct passwd account {};
    struct passwd* result = nullptr;
    char buffer[1024];
    if (getpwnam_r(kHelperAccount, &account, buffer, sizeof(buffer), &result) != 0 || result == nullptr)
        return false;
    return account.pw_uid != 0 && getuid() == account.pw_uid && geteuid() == account.pw_uid;
}

bool parse_target_uid(const char* value, uid_t& uid) {
    if (value == nullptr || *value == '\0')
        return false;
    for (const char* cursor = value; *cursor != '\0'; ++cursor) {
        if (*cursor < '0' || *cursor > '9')
            return false;
    }
    errno = 0;
    char* end = nullptr;
    const unsigned long long parsed = strtoull(value, &end, 10);
    if (errno != 0 || end == nullptr || *end != '\0' || parsed == 0 || parsed > std::numeric_limits<uid_t>::max())
        return false;
    uid = static_cast<uid_t>(parsed);
    return true;
}

bool peer_has_uid(int fd, uid_t expected_uid) {
    struct ucred credentials {};
    socklen_t length = sizeof(credentials);
    return getsockopt(fd, SOL_SOCKET, SO_PEERCRED, &credentials, &length) == 0 && length == sizeof(credentials) &&
           credentials.uid == expected_uid;
}

bool send_response(int fd, KbStatus status) {
    std::uint8_t bytes[KB_RESPONSE_BYTES] {};
    kb_encode_response({KB_PROTOCOL_VERSION, status}, bytes);
    return send(fd, bytes, sizeof(bytes), MSG_NOSIGNAL) == static_cast<ssize_t>(sizeof(bytes));
}

} // namespace

FdGuard::~FdGuard() {
    reset();
}

FdGuard::FdGuard(FdGuard&& other) noexcept : fd_(other.fd_) {
    other.fd_ = -1;
}

FdGuard& FdGuard::operator=(FdGuard&& other) noexcept {
    if (this != &other) {
        reset(other.fd_);
        other.fd_ = -1;
    }
    return *this;
}

void FdGuard::reset(int new_fd) {
    if (fd_ >= 0)
        close(fd_);
    fd_ = new_fd;
}

UinputDevice::~UinputDevice() {
    reset();
}

void UinputDevice::reset() {
    if (guard_.is_valid())
        ioctl(guard_.get(), UI_DEV_DESTROY);
    guard_.reset();
}

bool UinputDevice::initialize() {
    reset();
    const int fd = open("/dev/uinput", O_WRONLY | O_CLOEXEC);
    if (fd < 0)
        return false;
    guard_.reset(fd);

    if (ioctl(fd, UI_SET_EVBIT, EV_KEY) < 0 || ioctl(fd, UI_SET_KEYBIT, KEY_BACKSPACE) < 0 || ioctl(fd, UI_SET_KEYBIT, KEY_LEFT) < 0 ||
        ioctl(fd, UI_SET_KEYBIT, KEY_LEFTSHIFT) < 0 || ioctl(fd, UI_SET_KEYBIT, KEY_DELETE) < 0) {
        reset();
        return false;
    }

    struct uinput_setup setup {};
    setup.id.bustype = BUS_USB;
    setup.id.vendor = 0x4b45;
    setup.id.product = 0x4559;
    strncpy(setup.name, "fcitx5-evkey-server", UINPUT_MAX_NAME_SIZE - 1);
    if (ioctl(fd, UI_DEV_SETUP, &setup) < 0 || ioctl(fd, UI_DEV_CREATE) < 0) {
        reset();
        return false;
    }
    return true;
}

bool UinputDevice::send_tap(std::uint16_t code) {
    if (!guard_.is_valid())
        return false;
    struct input_event events[4] {};
    events[0].type = EV_KEY;
    events[0].code = code;
    events[0].value = 1;
    events[2].type = EV_KEY;
    events[2].code = code;
    return write_all(guard_.get(), events, sizeof(events));
}

bool UinputDevice::send_mod(std::uint16_t code, int value) {
    if (!guard_.is_valid())
        return false;
    struct input_event events[2] {};
    events[0].type = EV_KEY;
    events[0].code = code;
    events[0].value = value;
    return write_all(guard_.get(), events, sizeof(events));
}

bool UinputDevice::send_backspace() {
    return send_tap(KEY_BACKSPACE);
}

bool UinputDevice::send_delete() {
    return send_tap(KEY_DELETE);
}

bool UinputDevice::send_shift_down() {
    return send_mod(KEY_LEFTSHIFT, 1);
}

bool UinputDevice::send_shift_up() {
    return send_mod(KEY_LEFTSHIFT, 0);
}

bool UinputDevice::send_left() {
    return send_tap(KEY_LEFT);
}

LibinputContext::LibinputContext(const struct libinput_interface* interface) : udev_(udev_new()) {
    if (udev_ == nullptr)
        return;
    li_ = libinput_udev_create_context(interface, this, udev_);
    if (li_ != nullptr && libinput_udev_assign_seat(li_, "seat0") != 0) {
        libinput_unref(li_);
        li_ = nullptr;
    }
}

LibinputContext::~LibinputContext() {
    if (li_ != nullptr)
        libinput_unref(li_);
    if (udev_ != nullptr)
        udev_unref(udev_);
}

int LibinputContext::get_fd() const {
    return li_ == nullptr ? -1 : libinput_get_fd(li_);
}

void signal_handler(int sig) {
    if (sig == SIGTERM || sig == SIGINT)
        g_running.store(false);
}

int open_restricted(const char* path, int flags, void* user_data) {
    auto* context = static_cast<LibinputContext*>(user_data);
    if (context == nullptr || context->get_udev() == nullptr || path == nullptr)
        return -EPERM;

    struct stat status {};
    if (stat(path, &status) != 0 || !S_ISCHR(status.st_mode))
        return -EPERM;
    struct udev_device* device = udev_device_new_from_devnum(context->get_udev(), 'c', status.st_rdev);
    if (device == nullptr)
        return -EPERM;

    const char* seat = udev_device_get_property_value(device, "ID_SEAT");
    const bool pointer_class = property_is_one(device, "ID_INPUT_MOUSE") || property_is_one(device, "ID_INPUT_TOUCHPAD") ||
                               property_is_one(device, "ID_INPUT_POINTINGSTICK") || property_is_one(device, "ID_INPUT_TOUCHSCREEN");
    const bool allowed = seat != nullptr && strcmp(seat, "seat0") == 0 && pointer_class && !property_is_one(device, "ID_INPUT_KEYBOARD") &&
                         !is_helper_virtual_device(device);
    udev_device_unref(device);
    if (!allowed)
        return -EPERM;

    const int fd = open(path, flags | O_CLOEXEC);
    return fd < 0 ? -errno : fd;
}

void close_restricted(int fd, void*) {
    close(fd);
}

const struct libinput_interface interface = {
    .open_restricted = open_restricted,
    .close_restricted = close_restricted,
};

int main(int argc, char* argv[]) {
    uid_t target_uid = 0;
    if (argc != 3 || strcmp(argv[1], "--uid") != 0 || !parse_target_uid(argv[2], target_uid) || !helper_account_matches_process()) {
        LotusLogger::instance().error("Invalid helper identity or target UID");
        return 1;
    }

    const std::string uid_text = std::to_string(target_uid);
    const std::string keyboard_name = "evkey-" + uid_text + "-kb";
    const std::string pointer_name = "evkey-" + uid_text + "-pointer";
    if (keyboard_name.size() + 1 > UNIX_PATH_MAX || pointer_name.size() + 1 > UNIX_PATH_MAX) {
        LotusLogger::instance().error("Socket name exceeds abstract socket limit");
        return 1;
    }

    FdGuard keyboard_server(socket(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK | SOCK_CLOEXEC, 0));
    FdGuard pointer_server(socket(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK | SOCK_CLOEXEC, 0));
    if (!keyboard_server.is_valid() || !pointer_server.is_valid()) {
        LotusLogger::instance().error("Socket creation failed");
        return 1;
    }

    struct sockaddr_un keyboard_address {};
    keyboard_address.sun_family = AF_UNIX;
    keyboard_address.sun_path[0] = '\0';
    memcpy(keyboard_address.sun_path + 1, keyboard_name.data(), keyboard_name.size());
    struct sockaddr_un pointer_address {};
    pointer_address.sun_family = AF_UNIX;
    pointer_address.sun_path[0] = '\0';
    memcpy(pointer_address.sun_path + 1, pointer_name.data(), pointer_name.size());
    const socklen_t keyboard_length = offsetof(sockaddr_un, sun_path) + keyboard_name.size() + 1;
    const socklen_t pointer_length = offsetof(sockaddr_un, sun_path) + pointer_name.size() + 1;
    if (bind(keyboard_server.get(), reinterpret_cast<struct sockaddr*>(&keyboard_address), keyboard_length) != 0 ||
        bind(pointer_server.get(), reinterpret_cast<struct sockaddr*>(&pointer_address), pointer_length) != 0 || listen(keyboard_server.get(), 1) != 0 ||
        listen(pointer_server.get(), 1) != 0) {
        LotusLogger::instance().error("Socket setup failed");
        return 1;
    }

    SessionGate session(target_uid);
    if (!session.initialize()) {
        LotusLogger::instance().error("Unable to establish logind session policy");
        return 1;
    }
    LibinputContext libinput(&interface);
    if (!libinput.is_valid()) {
        LotusLogger::instance().error("Unable to establish pointer monitor");
        return 1;
    }

    struct sigaction action {};
    action.sa_handler = signal_handler;
    sigemptyset(&action.sa_mask);
    sigaction(SIGTERM, &action, nullptr);
    sigaction(SIGINT, &action, nullptr);

    enum class PendingPhase { None, Backspace, SelectLeft, SelectReleaseShift, SelectDelete, SelectFinalLeft };
    struct PendingInput {
        PendingPhase phase = PendingPhase::None;
        std::uint32_t remaining = 0;
        std::uint32_t post_delay = 0;
        std::chrono::steady_clock::time_point due {};
    } pending;

    UinputDevice uinput;
    FdGuard keyboard_client;
    FdGuard pointer_client;
    bool shift_held = false;
    std::set<struct libinput_device*> pointer_devices;

    auto abort_pending = [&]() {
        pending.phase = PendingPhase::None;
        pending.remaining = 0;
        bool released = true;
        if (shift_held) {
            released = uinput.send_shift_up();
            shift_held = false;
        }
        return released;
    };
    auto disconnect_keyboard = [&]() {
        if (!abort_pending())
            uinput.reset();
        keyboard_client.reset();
    };
    auto session_lost = [&]() {
        disconnect_keyboard();
        pointer_client.reset();
        uinput.reset();
    };
    auto ensure_uinput = [&]() { return uinput.get_fd() >= 0 || uinput.initialize(); };

    std::array<struct pollfd, 5> fds {};
    fds[0] = {keyboard_server.get(), POLLIN, 0};
    fds[1] = {libinput.get_fd(), POLLIN, 0};
    fds[2] = {pointer_server.get(), POLLIN, 0};

    while (g_running.load(std::memory_order_acquire)) {
        fds[3] = {keyboard_client.get(), POLLIN, 0};
        fds[4] = {session.fd(), session.events(), 0};
        int timeout = -1;
        if (pending.phase != PendingPhase::None) {
            const auto now = std::chrono::steady_clock::now();
            if (pending.due <= now)
                timeout = 0;
            else {
                const auto wait = std::chrono::duration_cast<std::chrono::milliseconds>(pending.due - now).count();
                timeout = wait >= INT_MAX ? INT_MAX : static_cast<int>(wait + 1);
            }
        }
        const int poll_result = poll(fds.data(), fds.size(), timeout);
        if (poll_result < 0) {
            if (errno == EINTR)
                continue;
            break;
        }
        if (!session.process()) {
            session_lost();
            break;
        }
        if (session.has_changed() && !session.check())
            session_lost();


        if ((fds[0].revents & POLLIN) != 0) {
            const int client = accept4(keyboard_server.get(), nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC);
            if (client >= 0) {
                if (!keyboard_client.is_valid() && peer_has_uid(client, target_uid))
                    keyboard_client.reset(client);
                else
                    close(client);
            }
        }
        if ((fds[2].revents & POLLIN) != 0) {
            const int client = accept4(pointer_server.get(), nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC);
            if (client >= 0) {
                if (!pointer_client.is_valid() && peer_has_uid(client, target_uid))
                    pointer_client.reset(client);
                else
                    close(client);
            }
        }

        if (keyboard_client.is_valid() && (fds[3].revents & (POLLIN | POLLHUP | POLLERR | POLLNVAL)) != 0) {
            std::uint8_t bytes[KB_REQUEST_BYTES + 1] {};
            const ssize_t received = recv(keyboard_client.get(), bytes, sizeof(bytes), MSG_TRUNC);
            if (received <= 0) {
                disconnect_keyboard();
            } else if (received != static_cast<ssize_t>(KB_REQUEST_BYTES)) {
                if (!send_response(keyboard_client.get(), KbStatus::InvalidRequest))
                    disconnect_keyboard();
            } else {
                std::uint8_t request_bytes[KB_REQUEST_BYTES] {};
                memcpy(request_bytes, bytes, sizeof(request_bytes));
                const KbRequest request = kb_decode_request(request_bytes);
                KbStatus status = KbStatus::InvalidRequest;
                bool close_after_response = false;
                if (kb_request_is_valid(request)) {
                    if (request.op == KbOp::Cancel) {
                        if (!abort_pending()) {
                            uinput.reset();
                            status = KbStatus::UnavailableDevice;
                        } else {
                            const bool active = session.check();
                            status = active ? KbStatus::Accepted : KbStatus::InactiveSession;
                            close_after_response = !active;
                        }
                    } else if (!session.check()) {
                        status = KbStatus::InactiveSession;
                        close_after_response = true;
                    } else if (request.op == KbOp::Probe) {
                        if (!ensure_uinput())
                            status = KbStatus::UnavailableDevice;
                        else if (pointer_devices.empty())
                            status = KbStatus::PointerUnavailable;
                        else
                            status = KbStatus::Accepted;
                    } else if (!ensure_uinput()) {
                        status = KbStatus::UnavailableDevice;
                    } else if (!abort_pending()) {
                        uinput.reset();
                        status = KbStatus::UnavailableDevice;
                    } else {
                        pending.remaining = request.count;
                        pending.post_delay = request.post_delay;
                        pending.due = std::chrono::steady_clock::now() + std::chrono::milliseconds(request.pre_delay);
                        pending.phase = request.op == KbOp::Backspace ? PendingPhase::Backspace : PendingPhase::SelectLeft;
                        if (request.op == KbOp::Select) {
                            if (!uinput.send_shift_down()) {
                                uinput.reset();
                                pending.phase = PendingPhase::None;
                                status = KbStatus::UnavailableDevice;
                            } else {
                                shift_held = true;
                                status = KbStatus::Accepted;
                            }
                        } else {
                            status = KbStatus::Accepted;
                        }
                    }
                }
                if (!send_response(keyboard_client.get(), status))
                    disconnect_keyboard();
                else if (close_after_response)
                    session_lost();
            }
        }

        if ((fds[1].revents & POLLIN) != 0)
            libinput_dispatch(libinput.get_li());
        struct libinput_event* event = nullptr;
        while ((event = libinput_get_event(libinput.get_li())) != nullptr) {
            const enum libinput_event_type type = libinput_event_get_type(event);
            struct libinput_device* device = libinput_event_get_device(event);
            if (type == LIBINPUT_EVENT_DEVICE_ADDED && device != nullptr) {
                if (libinput_device_has_capability(device, LIBINPUT_DEVICE_CAP_POINTER) || libinput_device_has_capability(device, LIBINPUT_DEVICE_CAP_TOUCH))
                    pointer_devices.insert(device);
            } else if (type == LIBINPUT_EVENT_DEVICE_REMOVED && device != nullptr) {
                pointer_devices.erase(device);
            } else if (type == LIBINPUT_EVENT_POINTER_BUTTON || type == LIBINPUT_EVENT_TOUCH_DOWN) {
                if (pointer_client.is_valid() && session.check()) {
                    const char reset = 'C';
                    if (send(pointer_client.get(), &reset, sizeof(reset), MSG_NOSIGNAL | MSG_DONTWAIT) != static_cast<ssize_t>(sizeof(reset)))
                        pointer_client.reset();
                }
            }
            libinput_event_destroy(event);
        }

        if (pending.phase != PendingPhase::None && pending.due <= std::chrono::steady_clock::now()) {
            if (!session.check()) {
                session_lost();
                continue;
            }
            if (!ensure_uinput()) {
                disconnect_keyboard();
                continue;
            }

            bool sent = true;
            const auto now = std::chrono::steady_clock::now();
            switch (pending.phase) {
                case PendingPhase::Backspace:
                    sent = uinput.send_backspace();
                    if (--pending.remaining == 0)
                        pending.phase = PendingPhase::None;
                    else
                        pending.due = now + std::chrono::milliseconds(pending.remaining == 1 ? pending.post_delay : 5);
                    break;
                case PendingPhase::SelectLeft:
                    sent = uinput.send_left();
                    if (--pending.remaining == 0) {
                        pending.phase = PendingPhase::SelectReleaseShift;
                        pending.due = now;
                    } else {
                        pending.due = now + std::chrono::milliseconds(8);
                    }
                    break;
                case PendingPhase::SelectReleaseShift:
                    sent = uinput.send_shift_up();
                    shift_held = false;
                    pending.phase = PendingPhase::SelectDelete;
                    pending.due = now;
                    break;
                case PendingPhase::SelectDelete:
                    sent = uinput.send_delete();
                    pending.phase = PendingPhase::SelectFinalLeft;
                    pending.due = now + std::chrono::milliseconds(pending.post_delay);
                    break;
                case PendingPhase::SelectFinalLeft:
                    sent = uinput.send_left();
                    pending.phase = PendingPhase::None;
                    break;
                case PendingPhase::None: break;
            }
            if (!sent) {
                disconnect_keyboard();
                uinput.reset();
            }
        }
    }

    abort_pending();
    uinput.reset();
    return 0;
}
