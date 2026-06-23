#!/usr/bin/env python3
"""Update package versions and hashes in this NUR repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALL_PACKAGES = sorted({"codex-switcher", "cosense-cli", "kimi-code", "manaba-cli"})


def run(
    cmd: list[str],
    *,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=check,
        text=True,
        stderr=subprocess.STDOUT if capture else None,
        stdout=subprocess.PIPE if capture else None,
    )


def read_json(url: str) -> object:
    headers = {"User-Agent": "Kyure-A/nur-packages updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def prefetch_hash(url: str, *, unpack: bool = False) -> str:
    cmd = ["nix", "store", "prefetch-file", "--json"]
    if unpack:
        cmd.append("--unpack")
    cmd.append(url)
    result = run(cmd, capture=True)
    return json.loads(result.stdout)["hash"]


def replace_once(text: str, pattern: str, replacement: str, *, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"pattern did not match exactly once: {pattern}")
    return updated


def update_npm_tarball(package: str, npm_name: str, tarball_name: str) -> None:
    metadata = read_json(f"https://registry.npmjs.org/{npm_name}")
    latest = metadata["dist-tags"]["latest"]  # type: ignore[index]
    tarball_url = f"https://registry.npmjs.org/{npm_name}/-/{tarball_name}-{latest}.tgz"
    source_hash = prefetch_hash(tarball_url)

    path = ROOT / "pkgs" / package / "default.nix"
    text = path.read_text()
    text = replace_once(text, r'version = "[^"]+";', f'version = "{latest}";')
    text = replace_once(text, r'hash = "sha256-[^"]+";', f'hash = "{source_hash}";')
    path.write_text(text)
    print(f"{package}: {latest}")


def update_codex_switcher() -> None:
    release = read_json("https://api.github.com/repos/Lampese/codex-switcher/releases/latest")
    tag = release["tag_name"]  # type: ignore[index]
    version = tag.removeprefix("v")
    assets = {
        asset["name"]: asset["browser_download_url"]  # type: ignore[index]
        for asset in release["assets"]  # type: ignore[index]
    }

    hashes = {
        "aarch64-darwin": prefetch_hash(assets["Codex.Switcher_aarch64.app.tar.gz"]),
        "x86_64-darwin": prefetch_hash(assets["Codex.Switcher_x64.app.tar.gz"]),
    }

    path = ROOT / "pkgs" / "codex-switcher" / "default.nix"
    text = path.read_text()
    text = replace_once(text, r'version = "[^"]+";', f'version = "{version}";')
    for system, source_hash in hashes.items():
        pattern = rf"({re.escape(system)} = \{{.*?hash = \")sha256-[^\"]+(\";)"
        text = replace_once(
            text,
            pattern,
            rf"\g<1>{source_hash}\2",
            flags=re.DOTALL,
        )
    path.write_text(text)
    print(f"codex-switcher: {version}")


def cargo_hash_for(package: str) -> str:
    result = run(["nix", "build", f".#{package}", "--no-link"], capture=True, check=False)
    output = result.stdout or ""
    match = re.search(r"got:\s+(sha256-[A-Za-z0-9+/=]+)", output)
    if not match:
        print(output)
        raise RuntimeError(f"could not extract cargo hash for {package}")
    return match.group(1)


def update_manaba_cli() -> None:
    metadata = read_json("https://crates.io/api/v1/crates/manaba-cli")
    latest = metadata["crate"]["max_stable_version"]  # type: ignore[index]
    crate_url = f"https://crates.io/api/v1/crates/manaba-cli/{latest}/download"
    source_hash = prefetch_hash(crate_url, unpack=True)

    path = ROOT / "pkgs" / "manaba-cli" / "default.nix"
    text = path.read_text()
    text = replace_once(text, r'version = "[^"]+";', f'version = "{latest}";')
    text = replace_once(
        text,
        r'src = fetchCrate \{\n    inherit pname version;\n    hash = "sha256-[^"]+";',
        'src = fetchCrate {\n    inherit pname version;\n    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";',
    )
    text = replace_once(
        text,
        r'cargoHash = "sha256-[^"]+";',
        'cargoHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";',
    )
    path.write_text(text)

    text = path.read_text()
    text = replace_once(
        text,
        r'src = fetchCrate \{\n    inherit pname version;\n    hash = "sha256-[^"]+";',
        f'src = fetchCrate {{\n    inherit pname version;\n    hash = "{source_hash}";',
    )
    path.write_text(text)

    cargo_hash = cargo_hash_for("manaba-cli")
    text = path.read_text()
    text = replace_once(
        text,
        r'cargoHash = "sha256-[^"]+";',
        f'cargoHash = "{cargo_hash}";',
    )
    path.write_text(text)
    print(f"manaba-cli: {latest}")


def update_package(package: str) -> None:
    if package == "kimi-code":
        update_npm_tarball(package, "@moonshot-ai/kimi-code", "kimi-code")
    elif package == "cosense-cli":
        update_npm_tarball(package, "@helpfeel/cosense-cli", "cosense-cli")
    elif package == "codex-switcher":
        update_codex_switcher()
    elif package == "manaba-cli":
        update_manaba_cli()
    else:
        raise ValueError(f"unknown package: {package}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "packages",
        nargs="*",
        help=f"packages to update, or empty for all: {', '.join(ALL_PACKAGES)}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packages = args.packages or ALL_PACKAGES
    unknown = sorted(set(packages) - set(ALL_PACKAGES))
    if unknown:
        print(f"unknown package(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    for package in packages:
        update_package(package)

    run(["nixpkgs-fmt", "default.nix", *[f"pkgs/{name}/default.nix" for name in packages]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
