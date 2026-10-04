set(EVKEY_ICON "${CMAKE_CURRENT_SOURCE_DIR}/icons/hicolor/scalable/apps/fcitx-evkey.svg")

install(FILES "${EVKEY_ICON}"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/apps"
    COMPONENT Runtime)
install(FILES "${EVKEY_ICON}"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/status"
    COMPONENT Runtime)

find_program(RSVG_CONVERT rsvg-convert REQUIRED)
set(EVKEY_PNG_OUTPUTS)
foreach(SIZE 22 24)
    set(OUT "${CMAKE_CURRENT_BINARY_DIR}/icons/hicolor/${SIZE}x${SIZE}/status/fcitx-evkey.png")
    add_custom_command(OUTPUT "${OUT}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/icons/hicolor/${SIZE}x${SIZE}/status"
        COMMAND ${RSVG_CONVERT} -w ${SIZE} -h ${SIZE} "${EVKEY_ICON}" -o "${OUT}"
        DEPENDS "${EVKEY_ICON}"
        COMMENT "Generating ${SIZE}px EVKey status icon")
    install(FILES "${OUT}"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/icons/hicolor/${SIZE}x${SIZE}/status"
        COMPONENT Runtime)
    list(APPEND EVKEY_PNG_OUTPUTS "${OUT}")
endforeach()
add_custom_target(evkey_icons ALL DEPENDS ${EVKEY_PNG_OUTPUTS})

install(FILES
    dictionaries/vietnamese.cm.dict
    dictionaries/LICENSE.vietnamese.cm.dict
    DESTINATION "${FCITX_INSTALL_PKGDATADIR}/evkey"
    COMPONENT Runtime)
