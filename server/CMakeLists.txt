find_package(PkgConfig REQUIRED)

pkg_check_modules(LIBINPUT REQUIRED IMPORTED_TARGET libinput)
pkg_check_modules(LIBUDEV REQUIRED IMPORTED_TARGET libudev)
pkg_check_modules(LIBSYSTEMD REQUIRED IMPORTED_TARGET libsystemd)

add_executable(fcitx5-evkey-server lotus-server.cpp lotus-logger.cpp)

target_link_libraries(fcitx5-evkey-server
    PkgConfig::LIBINPUT
    PkgConfig::LIBUDEV
    PkgConfig::LIBSYSTEMD
)

install(TARGETS fcitx5-evkey-server DESTINATION ${CMAKE_INSTALL_BINDIR} COMPONENT Uinput)
