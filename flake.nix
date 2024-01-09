{
  description = "A terminal Flamegraph viewer.";

  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
  flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs { inherit system; }; 
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
    in {
      packages = {
        flameshow = mkPoetryApplication { projectDir = self; };
        default = self.packages.${system}.flameshow;
      };

      devShells.default = pkgs.mkShell {
        packages = 
          (with pkgs; [ nil python3 mypy ruff poetry ]) 
          ++ 
          (with pkgs.python311Packages; [ pip python-lsp-server pylsp-mypy python-lsp-ruff ]);
      };
    }
  );
}
