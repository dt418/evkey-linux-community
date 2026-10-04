/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành <thanhpy2009@gmail.com>
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ  <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */
#include "lotus-monitor.h"
#include "lotus-utils.h"

#include <cstring>
#include <pwd.h>
#include <sys/socket.h>

bool authenticateMouseSocketPeer(int sock) {
    struct ucred cred{};
    socklen_t cred_len = sizeof(cred);
    if (getsockopt(sock, SOL_SOCKET, SO_PEERCRED, &cred, &cred_len) != 0) {
        LOTUS_ERROR("Failed to get peer credentials: " + std::string(strerror(errno)));
        return false;
    }

    const struct passwd* helper = getpwnam("evkey-input");
    return helper && helper->pw_uid != 0 && cred.uid == helper->pw_uid;
}
