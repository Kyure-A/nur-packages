{ lib
, rustPlatform
, fetchCrate
, git
, pkg-config
, openssl
,
}:

rustPlatform.buildRustPackage rec {
  pname = "manaba-cli";
  version = "0.9.2";

  src = fetchCrate {
    inherit pname version;
    hash = "sha256-g3RukgdU6tPv5mH5qcdjYe1PFE0GZJcJARgrxp7plIY=";
  };

  cargoHash = "sha256-JiR7ARDuk0her4Q2jTGRxQA6FLP2bC41LqWVMy7I4KM=";

  nativeBuildInputs = [
    git
    pkg-config
  ];

  buildInputs = [
    openssl
  ];

  meta = with lib; {
    description = "manaba for CLI";
    homepage = "https://github.com/crcrworks/manaba";
    license = licenses.mit;
    mainProgram = "manaba";
  };
}
