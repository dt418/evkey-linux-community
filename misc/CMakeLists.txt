set(EVKEY_INPUT_USER "evkey-input")

configure_file(99-evkey-uinput.rules.in
    ${CMAKE_CURRENT_BINARY_DIR}/99-evkey-uinput.rules @ONLY)
configure_file(fcitx5-evkey-server@.service.in
    ${CMAKE_CURRENT_BINARY_DIR}/fcitx5-evkey-server@.service @ONLY)
configure_file(evkey-input.conf.in
    ${CMAKE_CURRENT_BINARY_DIR}/evkey-input.conf @ONLY)

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/fcitx5-evkey-server@.service"
    DESTINATION lib/systemd/system
    COMPONENT Uinput)

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/99-evkey-uinput.rules"
    DESTINATION lib/udev/rules.d
    COMPONENT Uinput)

install(FILES module-fcitx5-evkey.conf
    DESTINATION lib/modules-load.d
    RENAME fcitx5-evkey.conf
    COMPONENT Uinput)

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/evkey-input.conf"
    DESTINATION lib/sysusers.d
    COMPONENT Uinput)
