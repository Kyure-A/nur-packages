{ lib
, stdenvNoCC
, fetchurl
,
}:

let
  version = "0.2.11";
  releases = {
    aarch64-darwin = {
      url = "https://github.com/Lampese/codex-switcher/releases/download/v${version}/Codex.Switcher_aarch64.app.tar.gz";
      hash = "sha256-RGN63aTlw8emLkFRpsiv6LtNv7u62fceizRq8xWfvt0=";
    };
    x86_64-darwin = {
      url = "https://github.com/Lampese/codex-switcher/releases/download/v${version}/Codex.Switcher_x64.app.tar.gz";
      hash = "sha256-oOA7mU/1T9tzvd6yNOw5nJh+X21E/cgu8eBw7RFREw8=";
    };
  };

  system = stdenvNoCC.hostPlatform.system;
  supported = releases ? ${system};
  release = releases.${system} or null;
in
stdenvNoCC.mkDerivation (
  {
    pname = "codex-switcher";
    inherit version;

    sourceRoot = ".";
    dontConfigure = true;
    dontBuild = true;
    dontUnpack = !supported;

    installPhase = ''
      runHook preInstall

      mkdir -p "$out/Applications" "$out/bin"
      cp -R "Codex Switcher.app" "$out/Applications/"

      cat > "$out/bin/codex-switcher" <<EOF
      #!/bin/sh
      exec "$out/Applications/Codex Switcher.app/Contents/MacOS/codex-switcher" "\$@"
      EOF
      chmod +x "$out/bin/codex-switcher"

      runHook postInstall
    '';

    meta = with lib; {
      description = "Desktop application for managing multiple OpenAI Codex CLI accounts";
      homepage = "https://github.com/Lampese/codex-switcher";
      license = licenses.unfree;
      mainProgram = "codex-switcher";
      platforms = builtins.attrNames releases;
      broken = !supported;
      sourceProvenance = [ sourceTypes.binaryNativeCode ];
    };
  }
    // lib.optionalAttrs supported {
    src = fetchurl {
      inherit (release) url hash;
    };
  }
)
