// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

/**
 * @file kb-socket-listener.h
 * @brief Shared helper for tests that observe addon requests to helper keyboard
 *        socket (`kb`).
 *
 * Tests bind abstract socket first, accept addon connection, decode exact
 * little-endian KbRequest frame, then acknowledge valid requests. This lets
 * addon event-loop response listener continue replacement processing.
 */

#include "lotus-protocol.h"
#include "lotus-utils.h"
#include "lotus-engine.h"
#include "lotus-state.h"


#include <cerrno>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <string>

#include <poll.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

inline void reportFailure(const std::string& step, const std::string& expected, const std::string& actual, const std::string& meaning) {
    std::cerr << "Step: " << step << '\n';
    std::cerr << "Expected: " << expected << '\n';
    std::cerr << "Actual: " << actual << '\n';
    std::cerr << "Meaning: " << meaning << '\n';
}

class KbSocketListener {
  public:
    KbSocketListener() : fd_(socket(AF_UNIX, SOCK_SEQPACKET, 0)) {

        if (fd_ < 0) {
            fail("socket");
            return;
        }
        sockaddr_un address{};
        address.sun_family    = AF_UNIX;
        const auto socketPath = buildSocketPath("kb");
        address.sun_path[0]   = '\0';
        std::memcpy(&address.sun_path[1], socketPath.data(), socketPath.size());
        const auto length = static_cast<socklen_t>(offsetof(sockaddr_un, sun_path) + socketPath.size() + 1);
        if (bind(fd_, reinterpret_cast<const sockaddr*>(&address), length) < 0 || listen(fd_, 5) < 0) {
            fail("bind/listen");
        }
    }

    ~KbSocketListener() {
        closeClient();
        if (fd_ >= 0)
            close(fd_);
    }

    KbSocketListener(const KbSocketListener&)            = delete;
    KbSocketListener& operator=(const KbSocketListener&) = delete;
    KbSocketListener(KbSocketListener&&)                 = delete;
    KbSocketListener& operator=(KbSocketListener&&)      = delete;

    bool receive(KbRequest& request, const char* meaning, const char* requestTimeoutExpected = "request within 5000 ms") {
        int remainingTimeout = kDefaultTimeoutMs;

        while (remainingTimeout > 0) {
            if (client_ < 0) {
                if (fd_ < 0) {
                    reportFailure("wait for replacement socket connection", "valid listener descriptor", "listener descriptor is invalid", meaning);
                    return false;
                }

                pollfd     pfd{fd_, POLLIN, 0};
                const auto pollResult = poll(&pfd, 1, remainingTimeout);
                if (pollResult == 0) {
                    reportFailure("wait for replacement socket connection", "connection request within timeout", "poll timed out", meaning);
                    return false;
                }
                if (pollResult < 0) {
                    if (errno == EINTR)
                        continue;
                    reportFailure("wait for replacement socket connection", "poll succeeds", "poll failed: " + std::string(std::strerror(errno)), meaning);
                    return false;
                }
                if ((pfd.revents & POLLIN) == 0) {
                    reportFailure("wait for replacement socket connection", "POLLIN revents", "revents=" + std::to_string(pfd.revents), meaning);
                    return false;
                }
                client_ = accept(fd_, nullptr, nullptr);
                if (client_ < 0) {
                    if (errno == EINTR || errno == EAGAIN)
                        continue;
                    reportFailure("accept replacement socket connection", "accept succeeds", "accept failed: " + std::string(std::strerror(errno)), meaning);
                    return false;
                }
            }

            pollfd     pfd{client_, POLLIN | POLLHUP | POLLRDHUP, 0};
            const auto pollResult = poll(&pfd, 1, remainingTimeout);
            if (pollResult == 0) {
                reportFailure("wait for replacement request", requestTimeoutExpected, "poll timed out", meaning);
                return false;
            }
            if (pollResult < 0) {
                if (errno == EINTR)
                    continue;
                reportFailure("wait for replacement request", "poll succeeds", "poll failed: " + std::string(std::strerror(errno)), meaning);
                return false;
            }
            if (((pfd.revents & (POLLHUP | POLLRDHUP)) != 0) && ((pfd.revents & POLLIN) == 0)) {
                closeClient();
                continue;
            }

            std::uint8_t bytes[KB_REQUEST_BYTES];
            const auto received = recv(client_, bytes, sizeof(bytes), MSG_TRUNC);
            if (received < 0) {
                if (errno == EINTR)
                    continue;
                reportFailure("receive replacement request", std::to_string(KB_REQUEST_BYTES) + " bytes",
                              "recv failed: " + std::string(std::strerror(errno)), meaning);
                return false;
            }
            if (received == 0) {
                // Socket closed by remote end
                closeClient();
                continue;
            }
            if (received != static_cast<ssize_t>(KB_REQUEST_BYTES)) {
                reportFailure("receive replacement request", std::to_string(KB_REQUEST_BYTES) + " bytes",
                              "recv returned " + std::to_string(received) + " bytes", meaning);
                return false;
            }

            request = kb_decode_request(bytes);
            if (!kb_request_is_valid(request)) {
                reportFailure("decode replacement request", "valid KbRequest v1",
                              "version=" + std::to_string(request.version) + ", op=" +
                                  std::to_string(static_cast<std::uint32_t>(request.op)) + ", count=" + std::to_string(request.count) +
                                  ", pre-delay=" + std::to_string(request.pre_delay) + ", post-delay=" + std::to_string(request.post_delay),
                              meaning);
                return false;
            }
            return sendAccepted(meaning);
        }

        reportFailure("wait for replacement request", requestTimeoutExpected, "timeout exceeded", meaning);
        return false;
    }

    bool valid() const {
        return fd_ >= 0;
    }


  private:
    static constexpr int kDefaultTimeoutMs = 5000;

    bool sendAccepted(const char* meaning) {
        const KbResponse response{KB_PROTOCOL_VERSION, KbStatus::Accepted};
        std::uint8_t     bytes[KB_RESPONSE_BYTES];
        kb_encode_response(response, bytes);
        const auto sent = send(client_, bytes, sizeof(bytes), MSG_NOSIGNAL);
        if (sent == static_cast<ssize_t>(sizeof(bytes)))
            return true;

        reportFailure("send replacement response", std::to_string(KB_RESPONSE_BYTES) + " bytes",
                      sent < 0 ? "send failed: " + std::string(std::strerror(errno)) : "send returned " + std::to_string(sent) + " bytes", meaning);
        return false;
    }
    void                 closeClient() {
        if (client_ >= 0) {
            close(client_);
            client_ = -1;
        }
    }

    void fail(const char* operation) {
        reportFailure(std::string(operation) + " replacement socket", "operation succeeds", std::string(operation) + " failed: " + std::strerror(errno),
                      "the test cannot observe replacement requests");
        close(fd_);
        fd_ = -1;
    }

    int fd_     = -1;
    int client_ = -1;
};

namespace fcitx {

struct LotusTestAccess {
    static bool completeResponse(LotusEngine& engine, InputContext& ic, const char* meaning) {
        auto* state = ic.propertyFor(&engine.factory_);
        if (state == nullptr) {
            reportFailure("complete helper response", "input-context state exists", "state is null", meaning);
            return false;
        }

        std::uint8_t responseBytes[KB_RESPONSE_BYTES];
        const auto   received = recv(uinput_client_fd_.load(std::memory_order_acquire), responseBytes, sizeof(responseBytes), MSG_DONTWAIT | MSG_TRUNC);
        if (received != static_cast<ssize_t>(KB_RESPONSE_BYTES)) {
            reportFailure("receive helper response", std::to_string(KB_RESPONSE_BYTES) + " bytes",
                          "recv returned " + std::to_string(received), meaning);
            return false;
        }
        const auto response = kb_decode_response(responseBytes);
        if (!kb_response_is_valid(response) || response.status != KbStatus::Accepted) {
            reportFailure("validate helper response", "status=Accepted",
                          "status=" + std::to_string(static_cast<std::uint32_t>(response.status)), meaning);
            return false;
        }

        const bool probe = state->pendingHelperOp_ == KbOp::Probe;
        state->kbResponseTimeoutSource_.reset();
        state->kbResponseEventSource_.reset();
        state->helperRequestPending_ = false;
        if (probe) {
            state->probePending_ = false;
            state->helperReady_ = true;
            state->helperProbeFailed_ = false;
            state->effectiveMode_ = state->requestedMode_;
            state->modeReason_.clear();
        }
        return true;
    }

    static bool completeProbe(KbSocketListener& listener, LotusEngine& engine, InputContext& ic, const char* meaning) {
        KbRequest request{};
        if (!listener.receive(request, meaning))
            return false;
        if (request.op != KbOp::Probe) {
            reportFailure("complete helper probe", "op=Probe", "op=" + std::to_string(static_cast<std::uint32_t>(request.op)), meaning);
            return false;
        }
        return completeResponse(engine, ic, meaning);
    }
};

} // namespace fcitx
