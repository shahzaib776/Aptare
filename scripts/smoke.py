"""End-to-end check of the running compose stack (`make smoke`): Phase 1's exit criterion.

Renders a resume through the web server, downloads the PDF and compares its hash, then checks
the network rules around the compile worker (rule 12). Standard library only.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8080")

RESUME = {
    "header": {"full_name": "Ada Lovelace", "email": "ada@example.com"},
    "summary": "Builds reliable systems.",
    "sections": [
        {
            "key": "experience",
            "items": [
                {
                    "experience_id": "00000000-0000-4000-8000-000000000001",
                    "variant_id": "00000000-0000-4000-8000-000000000002",
                    "title": "Engineer",
                    "company": "Analytical Engines",
                    "dates": "2020 - Present",
                    "bullets": [
                        {
                            "id": "00000000-0000-4000-8000-000000000010",
                            "source_bullet_id": "00000000-0000-4000-8000-000000000110",
                            "text": "Cut costs by 30% with a multi-threaded rewrite",
                            "stretched_terms": [],
                            "covered_keywords": [],
                        }
                    ],
                }
            ],
        }
    ],
}

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{' - ' + detail if detail and not ok else ''}")
    if not ok:
        failures.append(name)


def get(path: str) -> tuple[int, dict[str, str], bytes]:
    with urllib.request.urlopen(BASE + path, timeout=30) as response:
        return response.status, dict(response.headers), response.read()


def post_json(path: str, body: object) -> dict[str, object]:
    request = urllib.request.Request(
        BASE + path,
        json.dumps(body).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result: dict[str, object] = json.load(response)
        return result


def exec_in(service: str, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "exec", "-T", service, *command],
        capture_output=True,
        text=True,
        timeout=60,
    )


def main() -> int:
    status, _, page = get("/")
    check("the web server serves the app", status == 200 and b'id="root"' in page)
    status, _, page = get("/dev/render")
    check("a deep link falls back to the app", status == 200 and b'id="root"' in page)

    # pdf.js starts a module worker, and browsers refuse one that is not labelled JavaScript.
    script = re.search(rb'src="(/assets/[^"]+\.js)"', page)
    _, _, code = get(script.group(1).decode()) if script else (0, {}, b"")
    workers = sorted(set(re.findall(rb"assets/[\w.-]+\.mjs", code)))
    types = {w.decode(): get("/" + w.decode())[1].get("Content-Type", "") for w in workers}
    check(
        "the pdf.js worker is served as JavaScript",
        bool(types) and all("javascript" in kind for kind in types.values()),
        str(types),
    )

    _, _, body = get("/api/v1/health")
    check("the API reaches the compiler", json.loads(body) == {"status": "ok", "compiler": "ok"})

    render = post_json("/api/v1/dev/render", {"resume": RESUME, "template_id": "dense-single"})
    check("a resume renders to a PDF", render["page_count"] == 1, str(render))
    pdf_hash = str(render["pdf_hash"])
    text_map = render["text_map"]
    check(
        "the bullet gets click regions",
        isinstance(text_map, dict) and bool(text_map.get("00000000-0000-4000-8000-000000000010")),
    )

    status, headers, pdf = get(f"/api/v1/files/pdf/{pdf_hash}")
    check("the PDF downloads", status == 200 and headers.get("Content-Type") == "application/pdf")
    check("the download is byte-identical to its hash", hashlib.sha256(pdf).hexdigest() == pdf_hash)

    again = post_json("/api/v1/dev/render", {"resume": RESUME, "template_id": "dense-single"})
    check("rendering again gives the same hashes", again == render)

    # Each isolation check first proves its tool works (the "control"), so a missing program
    # or a typo cannot make a blocked connection look like a pass.
    no_internet = exec_in(
        "compiler",
        "python",
        "-c",
        "import socket; socket.create_connection(('127.0.0.1', 8001), 3); print('control-ok'); "
        "socket.create_connection(('1.1.1.1', 443), 3)",
    )
    check(
        "the compiler cannot reach the internet",
        "control-ok" in no_internet.stdout and no_internet.returncode != 0,
        no_internet.stderr,
    )

    api_to_compiler = exec_in(
        "api",
        "python",
        "-c",
        "import urllib.request; urllib.request.urlopen('http://compiler:8001/health', timeout=5)",
    )
    check("the API can reach the compiler", api_to_compiler.returncode == 0, api_to_compiler.stderr)

    web_to_compiler = exec_in(
        "frontend",
        "sh",
        "-c",
        "wget -q -T 3 -O /dev/null http://api:8000/api/v1/health && echo control-ok; "
        "wget -q -T 3 -O /dev/null http://compiler:8001/health",
    )
    check(
        "the web server cannot reach the compiler",
        "control-ok" in web_to_compiler.stdout and web_to_compiler.returncode != 0,
        web_to_compiler.stderr,
    )

    port = subprocess.run(
        ["docker", "compose", "port", "frontend", "8080"], capture_output=True, text=True
    )
    check(
        "the app is offered to this machine only",
        port.stdout.startswith("127.0.0.1:"),
        port.stdout.strip(),
    )

    print(f"\n{'all checks passed' if not failures else str(len(failures)) + ' check(s) failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.URLError as error:
        print(f"FAIL  cannot reach {BASE}: {error.reason}")
        sys.exit(1)
