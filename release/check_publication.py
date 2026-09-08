"""Reject private paths in the Git index and broken public Markdown links."""

from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def git(*args, **kwargs):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=False,
                          capture_output=True, **kwargs)


def main():
    listing = git("ls-files", "-z")
    if listing.returncode:
        raise SystemExit(listing.stderr.decode())
    paths = [p.decode() for p in listing.stdout.split(b"\0") if p]
    ignored = git("check-ignore", "--no-index", "--stdin", "-z", input=listing.stdout)
    if ignored.returncode not in (0, 1):
        raise SystemExit(ignored.stderr.decode())
    private = {p.decode() for p in ignored.stdout.split(b"\0") if p}
    problems = [f"Private/generated file tracked: {p}" for p in private]
    public = set(paths)
    for name in paths:
        if name in private or not name.endswith(".md"):
            continue
        content = (ROOT / name).read_text()
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
            target = target.strip().split(' "', 1)[0].strip("<>")
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not target:
                continue
            resolved = (ROOT / name).parent.joinpath(target).resolve()
            try:
                relative = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                problems.append(f"Local-only link: {name} -> {target}")
                continue
            if relative not in public and not any(p.startswith(relative + "/") for p in public):
                problems.append(f"Unpublished link: {name} -> {target}")
    if problems:
        raise SystemExit("\n".join(sorted(set(problems))))
    print(f"PASS: {len(paths)} tracked files; no ignored files or broken public Markdown paths")


if __name__ == "__main__":
    main()
