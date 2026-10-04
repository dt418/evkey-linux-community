{ config, lib, pkgs, ... }:

let
  inherit (lib) mkEnableOption mkIf mkOption optional types;
  cfg = config.programs.fcitx5-evkey;
in
{
  options.programs.fcitx5-evkey = {
    enable = mkEnableOption "EVKey Linux Community for Fcitx 5";

    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ./package.nix { src = ../..; };
      defaultText = "pkgs.callPackage packaging/nix/package.nix { }";
      description = "EVKey Linux Community package; includes separate runtime and uinput outputs.";
    };

    uinput.enable = mkEnableOption "the optional EVKey Smooth-mode uinput helper";
  };

  config = mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ]
      ++ optional cfg.uinput.enable cfg.package.uinput;

    systemd.packages = optional cfg.uinput.enable cfg.package.uinput;

    boot.kernelModules = lib.mkIf cfg.uinput.enable [ "uinput" ];

    users.groups.evkey-input = lib.mkIf cfg.uinput.enable { };
    users.users.evkey-input = lib.mkIf cfg.uinput.enable {
      isSystemUser = true;
      group = "evkey-input";
      description = "EVKey uinput helper";
      home = "/var/empty";
      createHome = false;
      shell = "${pkgs.shadow}/bin/nologin";
    };

    services.udev.extraRules = lib.mkIf cfg.uinput.enable ''
      KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput"
      ACTION=="add|change", KERNEL=="uinput", SUBSYSTEM=="misc", RUN+="${pkgs.acl}/bin/setfacl -m u:evkey-input:rw $env{DEVNAME}"
      ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_SEAT}=="seat0", ENV{ID_INPUT_KEYBOARD}!="1", ENV{ID_INPUT_MOUSE}=="1", RUN+="${pkgs.acl}/bin/setfacl -m u:evkey-input:r $env{DEVNAME}"
      ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_SEAT}=="seat0", ENV{ID_INPUT_KEYBOARD}!="1", ENV{ID_INPUT_TOUCHPAD}=="1", RUN+="${pkgs.acl}/bin/setfacl -m u:evkey-input:r $env{DEVNAME}"
      ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_SEAT}=="seat0", ENV{ID_INPUT_KEYBOARD}!="1", ENV{ID_INPUT_POINTINGSTICK}=="1", RUN+="${pkgs.acl}/bin/setfacl -m u:evkey-input:r $env{DEVNAME}"
      ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_SEAT}=="seat0", ENV{ID_INPUT_KEYBOARD}!="1", ENV{ID_INPUT_TOUCHSCREEN}=="1", RUN+="${pkgs.acl}/bin/setfacl -m u:evkey-input:r $env{DEVNAME}"
    '';
  };
}
