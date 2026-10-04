#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Development-only checks. No package installation or system mutation.
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(CDPATH= cd -- "$script_dir/.." && pwd -P)"

usage() {
    printf '%s\n' \
        'Usage: tools/dev.sh <help|check|dbus>' \
        '       tools/dev.sh settings [unittest.dotted.selector ...]' \
        '' \
        'Commands:' \
        '  help      Show this usage without checking dependencies.' \
        '  check     Configure, build, run CTest and both Go test suites, then validate translations.' \
        '  settings  Run Settings GUI suite with Qt offscreen; accepts optional unittest selectors.' \
        '  dbus      Run isolated mocked D-Bus owner-recovery test.' \
        '' \
        'Environment:' \
        '  BUILD_DIR Build directory (default: <repo>/build/dev).' \
        '  JOBS      Positive parallel-job count (default: detected CPUs, capped at 4).' \
        '  PYTHON    Python executable (default: python3).'
}

fail_usage() {
    printf 'error: %s\n' "$1" >&2
    usage >&2
    exit 2
}

resolve_build_dir() {
    build_dir="${BUILD_DIR:-$repo_root/build/dev}"
    case "$build_dir" in
        /*) ;;
        *) build_dir="$repo_root/$build_dir" ;;
    esac
}

resolve_jobs() {
    if [[ -n "${JOBS:-}" ]]; then
        jobs="$JOBS"
    elif command -v getconf >/dev/null 2>&1; then
        jobs="$(getconf _NPROCESSORS_ONLN 2>/dev/null || printf '2')"
    elif command -v nproc >/dev/null 2>&1; then
        jobs="$(nproc 2>/dev/null || printf '2')"
    else
        jobs=2
    fi

    [[ "$jobs" =~ ^[1-9][0-9]*$ ]] || {
        printf 'error: JOBS must be a positive integer\n' >&2
        exit 2
    }
    if (( jobs > 4 )); then
        jobs=4
    fi
}

check_translations() {
    local catalog output_dir catalog_name
    local -a catalogs

    shopt -s nullglob
    catalogs=("$repo_root"/po/*.po)
    shopt -u nullglob
    ((${#catalogs[@]})) || {
        printf 'error: no PO catalogues found under po/\n' >&2
        return 1
    }

    output_dir="$(mktemp -d "${TMPDIR:-/tmp}/evkey-msgfmt.XXXXXX")"
    trap 'rm -rf -- "$output_dir"' RETURN
    for catalog in "${catalogs[@]}"; do
        catalog_name="$(basename "${catalog%.po}")"
        msgfmt --check --output-file "$output_dir/$catalog_name.mo" "$catalog"
    done
    trap - RETURN
    rm -rf -- "$output_dir"
}

run_check() {
    resolve_build_dir
    resolve_jobs

    cmake -S "$repo_root" -B "$build_dir" \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_INSTALL_PREFIX=/usr \
        -DBUILD_TESTING=ON
    cmake --build "$build_dir" --parallel "$jobs"
    ctest --test-dir "$build_dir" --output-on-failure --parallel "$jobs"
    (
        cd "$repo_root/bamboo"
        go test ./...
    )
    (
        cd "$repo_root/bamboo/bamboo-core"
        go test ./...
    )
    check_translations
}

run_settings() {
    local python_path="${PYTHON:-python3}"
    QT_QPA_PLATFORM=offscreen \
        PYTHONPATH="$repo_root/settings-gui${PYTHONPATH:+:$PYTHONPATH}" \
        "$python_path" "$repo_root/test/settings-gui-startup.py" "$@"
}

run_dbus() {
    local python_path="${PYTHON:-python3}"
    dbus-run-session -- env \
        "PYTHONPATH=$repo_root/settings-gui${PYTHONPATH:+:$PYTHONPATH}" \
        "$python_path" "$repo_root/test/settings-gui-dbus-owner-recovery.py"
}

case "${1:-help}" in
    help|--help|-h)
        (($# <= 1)) || fail_usage 'help takes no arguments'
        usage
        ;;
    check)
        (($# == 1)) || fail_usage 'check takes no arguments'
        run_check
        ;;
    settings)
        shift
        run_settings "$@"
        ;;
    dbus)
        (($# == 1)) || fail_usage 'dbus takes no arguments'
        run_dbus
        ;;
    *)
        fail_usage "unknown command: $1"
        ;;
esac
