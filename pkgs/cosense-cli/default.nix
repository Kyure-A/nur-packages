{ lib
, stdenvNoCC
, fetchurl
, makeWrapper
, tsx
,
}:

stdenvNoCC.mkDerivation rec {
  pname = "cosense-cli";
  version = "1.4.6";

  src = fetchurl {
    url = "https://registry.npmjs.org/@helpfeel/cosense-cli/-/cosense-cli-${version}.tgz";
    hash = "sha256-dE6e2nbUdXABnhMy82tvluHmMN5KLpwr904+gszCq0g=";
  };

  sourceRoot = "package";

  nativeBuildInputs = [
    makeWrapper
  ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/lib/cosense-cli" "$out/bin"
    cp -R README.md package.json src "$out/lib/cosense-cli/"

    makeWrapper "${tsx}/bin/tsx" "$out/bin/cosense" \
      --add-flags "$out/lib/cosense-cli/src/cli.ts"

    runHook postInstall
  '';

  meta = with lib; {
    description = "CLI for reading, searching, and editing Cosense pages";
    homepage = "https://github.com/helpfeel/cosense-cli";
    license = licenses.mit;
    mainProgram = "cosense";
  };
}
