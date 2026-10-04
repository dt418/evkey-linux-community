add_library(evkey MODULE lotus.cpp ${fcitx_lotus_core_sources})
set_target_properties(evkey PROPERTIES OUTPUT_NAME "evkey")
set_target_properties(evkey PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_options(evkey PRIVATE "-Wl,-exclude-libs,ALL")
target_link_libraries(evkey
    Fcitx5::Core
    Fcitx5::Config
    Fcitx5::Module::Emoji
    Bamboo::Core
    Pthread::Pthread
)

target_include_directories(evkey PRIVATE
    ${PROJECT_BINARY_DIR}
)
target_compile_definitions(evkey PRIVATE
    EVKEY_SETTINGS_PATH="${CMAKE_INSTALL_FULL_BINDIR}/fcitx5-evkey-settings"
)
install(TARGETS evkey DESTINATION "${CMAKE_INSTALL_LIBDIR}/fcitx5" COMPONENT Runtime)

fcitx5_translate_desktop_file(evkey.conf.in evkey.conf)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/evkey.conf"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/fcitx5/inputmethod"
        COMPONENT Runtime)
configure_file(evkey-addon.conf.in.in ${CMAKE_CURRENT_BINARY_DIR}/evkey-addon.conf.in)
fcitx5_translate_desktop_file("${CMAKE_CURRENT_BINARY_DIR}/evkey-addon.conf.in" evkey-addon.conf)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/evkey-addon.conf"
        RENAME evkey.conf
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon"
        COMPONENT Runtime)
