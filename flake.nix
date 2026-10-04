{
  description = "EVKey Linux Community, Fcitx 5 Vietnamese input method";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          evkey = pkgs.callPackage ./packaging/nix/package.nix { src = self; };
        in
        {
          default = evkey;
          fcitx5-evkey = evkey;
        });

      nixosModules.default = import ./packaging/nix/module.nix;
    };
}
