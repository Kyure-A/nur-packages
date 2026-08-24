{ lib
, stdenvNoCC
, fetchurl
, makeWrapper
, nodejs
,
}:

stdenvNoCC.mkDerivation rec {
  pname = "kimi-code";
  version = "0.38.0";

  src = fetchurl {
    url = "https://registry.npmjs.org/@moonshot-ai/kimi-code/-/kimi-code-${version}.tgz";
    hash = "sha256-1cBH2/u9/d+NIAMDJ+cj6pEhr2YmCYOoVWEkWA1ktUk=";
  };

  sourceRoot = "package";

  nativeBuildInputs = [
    makeWrapper
  ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/lib/kimi-code" "$out/bin"
    cp -R dist package.json scripts README.md LICENSE "$out/lib/kimi-code/"
    makeWrapper "${nodejs}/bin/node" "$out/bin/kimi" \
      --add-flags "$out/lib/kimi-code/dist/main.mjs"

    runHook postInstall
  '';

  meta = with lib; {
    description = "Terminal AI coding agent from Moonshot AI";
    homepage = "https://github.com/MoonshotAI/kimi-code";
    license = licenses.mit;
    mainProgram = "kimi";
    platforms = nodejs.meta.platforms;
  };
}
