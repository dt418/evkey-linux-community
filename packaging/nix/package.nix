{ stdenv
, lib
, cmake
, extra-cmake-modules
, gettext
, go
, pkg-config
, python3
, python3Packages
, librsvg
, makeWrapper
, fcitx5
, libinput
, systemd
, acl
, src
}:

let
  source = src;
in
stdenv.mkDerivation rec {
  pname = "fcitx5-evkey";
  version = "1.0.0";
  src = lib.cleanSourceWith {
    src = source;
    filter = path: type:
      let
        pathString = toString path;
        relative = lib.removePrefix (toString source + "/") pathString;
        topLevel = builtins.head (lib.splitString "/" relative);
        baseName = builtins.baseNameOf pathString;
      in
        pathString == toString source
        || (
          !(lib.elem topLevel [ ".git" "build" "debian" "dist" "obj-x86_64-linux-gnu" ])
          && !(lib.elem baseName [ ".git" "__pycache__" ])
          && !(lib.hasSuffix ".tar.gz" baseName)
          && !(lib.hasSuffix ".tar.bz2" baseName)
          && !(lib.hasSuffix ".deb" baseName)
        );
  };

  outputs = [ "out" "uinput" ];

  nativeBuildInputs = [
    cmake
    extra-cmake-modules
    gettext
    go
    pkg-config
    python3
    librsvg
    makeWrapper
  ];

  buildInputs = [
    fcitx5
    libinput
    systemd
    acl
    python3Packages.dbus-python
    python3Packages.pyqt5
    python3Packages.qtpy
  ];

  cmakeFlags = [
    "-DCMAKE_INSTALL_PREFIX=${placeholder "out"}"
    "-DCMAKE_INSTALL_LIBDIR=lib"
    "-DCMAKE_BUILD_TYPE=Release"
    "-DBUILD_TESTING=OFF"
    "-DEVKEY_BYTECOMPILE_PYTHON=OFF"
  ];

  preBuild = ''
    export GOCACHE="$TMPDIR/go-build"
    export GOPATH="$TMPDIR/go"
    mkdir -p "$GOCACHE" "$GOPATH"
  '';

  installPhase = ''
    runHook preInstall
    cmake --install . --component Runtime --prefix "$out"
    cmake --install . --component Uinput --prefix "$uinput"
    runHook postInstall
  '';

  postInstall = ''
    mkdir -p "$uinput/bin"
    mv "$out/bin/fcitx5-evkey-server" "$uinput/bin/"
    wrapProgram "$out/bin/fcitx5-evkey-settings" \
      --prefix PATH : "${python3}/bin" \
      --prefix PYTHONPATH : "${python3Packages.makePythonPath [
        python3Packages.dbus-python
        python3Packages.pyqt5
        python3Packages.qtpy
      ]}"
    substituteInPlace "$uinput/lib/systemd/system/fcitx5-evkey-server@.service" \
      --replace-fail /usr/bin/fcitx5-evkey-server "$uinput/bin/fcitx5-evkey-server"
    substituteInPlace "$uinput/lib/udev/rules.d/99-evkey-uinput.rules" \
      --replace-fail /usr/bin/setfacl "${acl}/bin/setfacl"
  '';

  meta = {
    description = "EVKey Linux Community Vietnamese input method for Fcitx 5";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
