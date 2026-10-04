/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

#ifndef _LOTUS_PROTOCOL_H_
#define _LOTUS_PROTOCOL_H_

#include <cstddef>
#include <cstdint>

constexpr std::uint32_t KB_PROTOCOL_VERSION = 1;
constexpr std::size_t KB_REQUEST_BYTES = 20;
constexpr std::size_t KB_RESPONSE_BYTES = 8;
constexpr std::uint32_t KB_MAX_COUNT = 256;
constexpr std::uint32_t KB_MAX_DELAY_MS = 1000;

enum class KbOp : std::uint32_t {
    Backspace = 0,
    Select = 1,
    Cancel = 2,
    Probe = 3,
};

enum class KbStatus : std::uint32_t {
    Accepted = 0,
    InactiveSession = 1,
    UnavailableDevice = 2,
    InvalidRequest = 3,
    PointerUnavailable = 4,
};

struct KbRequest {
    std::uint32_t version;
    KbOp op;
    std::uint32_t count;
    std::uint32_t pre_delay;
    std::uint32_t post_delay;
};

struct KbResponse {
    std::uint32_t version;
    KbStatus status;
};

inline std::uint32_t kb_read_le32(const std::uint8_t* bytes) {
    return static_cast<std::uint32_t>(bytes[0]) |
           (static_cast<std::uint32_t>(bytes[1]) << 8U) |
           (static_cast<std::uint32_t>(bytes[2]) << 16U) |
           (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

inline void kb_write_le32(std::uint8_t* bytes, std::uint32_t value) {
    bytes[0] = static_cast<std::uint8_t>(value);
    bytes[1] = static_cast<std::uint8_t>(value >> 8U);
    bytes[2] = static_cast<std::uint8_t>(value >> 16U);
    bytes[3] = static_cast<std::uint8_t>(value >> 24U);
}

inline KbRequest kb_decode_request(const std::uint8_t (&bytes)[KB_REQUEST_BYTES]) {
    return {kb_read_le32(bytes), static_cast<KbOp>(kb_read_le32(bytes + 4)), kb_read_le32(bytes + 8),
            kb_read_le32(bytes + 12), kb_read_le32(bytes + 16)};
}

inline void kb_encode_request(const KbRequest& request, std::uint8_t (&bytes)[KB_REQUEST_BYTES]) {
    kb_write_le32(bytes, request.version);
    kb_write_le32(bytes + 4, static_cast<std::uint32_t>(request.op));
    kb_write_le32(bytes + 8, request.count);
    kb_write_le32(bytes + 12, request.pre_delay);
    kb_write_le32(bytes + 16, request.post_delay);
}

inline void kb_encode_response(const KbResponse& response, std::uint8_t (&bytes)[KB_RESPONSE_BYTES]) {
    kb_write_le32(bytes, response.version);
    kb_write_le32(bytes + 4, static_cast<std::uint32_t>(response.status));
}

inline KbResponse kb_decode_response(const std::uint8_t (&bytes)[KB_RESPONSE_BYTES]) {
    return {kb_read_le32(bytes), static_cast<KbStatus>(kb_read_le32(bytes + 4))};
}

inline bool kb_response_is_valid(const KbResponse& response) {
    return response.version == KB_PROTOCOL_VERSION && static_cast<std::uint32_t>(response.status) <= static_cast<std::uint32_t>(KbStatus::PointerUnavailable);
}

inline bool kb_request_is_valid(const KbRequest& request) {
    if (request.version != KB_PROTOCOL_VERSION || request.pre_delay > KB_MAX_DELAY_MS || request.post_delay > KB_MAX_DELAY_MS)
        return false;

    switch (request.op) {
        case KbOp::Backspace:
        case KbOp::Select:
            return request.count >= 1 && request.count <= KB_MAX_COUNT;
        case KbOp::Cancel:
        case KbOp::Probe:
            return request.count == 0 && request.pre_delay == 0 && request.post_delay == 0;
    }
    return false;
}

#endif // _LOTUS_PROTOCOL_H_
