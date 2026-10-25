"""Register/verify local C64 analysis media. Standard library only; no downloads."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reference" / "manifest.json"


def digest(path):
    with path.open("rb") as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
        return result.hexdigest()


def register(source, manifest):
    primary = manifest["primary"]
    source = Path(source).resolve(strict=True)
    with source.open("rb") as stream:
        if stream.read(8) != b"GCR-1541":
            raise ValueError("Expected a G64 file with GCR-1541 signature.")
    original = ROOT / primary["original_path"]
    working = ROOT / primary["working_path"]
    if original.exists() or working.exists() or primary["sha256"] is not None:
        raise ValueError("Reference already exists or is hash-locked; refusing replacement.")
    sha256 = digest(source)
    for target in (original, working):
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also guards against accidental replacement.
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        if digest(target) != sha256:
            raise ValueError(f"Copy verification failed: {target}")
    original.chmod(stat.S_IREAD)
    primary.update(sha256=sha256, size_bytes=original.stat().st_size,
                   acquisition_status="registered_local_copy",
                   edition_verification_status="pending_manual_verification",
                   boot_status="not_run", blocker=None)
    # Write manifest only once both copies have been checked.
    temporary = MANIFEST.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST)
    print(f"Registered SHA-256 {sha256}")
    print("Edition and boot verification remain pending. Record provenance before capture.")


def verify(manifest, candidate_only=False):
    failed = False
    primary = manifest["primary"]
    if candidate_only:
        candidate = manifest.get("analysis_candidate")
        if not candidate:
            print("FAIL: no registered analysis candidate")
            failed = True
        else:
            for path_key, hash_key in (("container_path", "container_sha256"),
                    ("working_prg_path", "working_prg_sha256"),
                    ("baseline_snapshot_path", "baseline_snapshot_sha256")):
                path = ROOT / candidate[path_key]
                if not path.is_file() or digest(path) != candidate[hash_key]:
                    print(f"FAIL candidate: {path_key}")
                    failed = True
            if not failed:
                print("OK candidate identities; original edition and gameplay parity remain unverified")
    elif primary["sha256"] is None:
        print(f"PENDING primary: {primary['acquisition_status']} (no hash lock)")
        failed = True
    else:
        original = ROOT / primary["original_path"]
        if (not original.is_file() or digest(original) != primary["sha256"]
                or original.stat().st_size != primary["size_bytes"]):
            print("FAIL primary: original missing or changed")
            failed = True
        else:
            print("OK primary identity; this does not verify edition or boot")
    secondary = manifest["secondary"]
    base = ROOT / secondary["local_path"]
    if not secondary["files"]:
        print("PENDING secondary file inventory")
        failed = True
    for entry in secondary["files"]:
        path = base / entry["path"]
        if (not path.is_file() or digest(path) != entry["sha256"]
                or path.stat().st_size != entry["size_bytes"]):
            print(f"FAIL secondary: {entry['path']}")
            failed = True
    if secondary["files"]:
        print(f"Checked {len(secondary['files'])} secondary file identities")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verification = commands.add_parser("verify")
    verification.add_argument("--candidate", action="store_true",
                              help="Verify the local analysis candidate instead of missing preservation media")
    registration = commands.add_parser("register")
    registration.add_argument("source", help="Authorized copy of selected original G64")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    try:
        if args.command == "register":
            register(args.source, manifest)
            return 0
        return verify(manifest, args.candidate)
    except (OSError, ValueError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
