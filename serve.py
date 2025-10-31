"""간단한 정적 웹 서버로 `docs/` 대시보드를 서빙합니다.

이 스크립트는 Python 표준 라이브러리만을 사용하여 효율적 프런티어 분석 결과를 담은
웹 대시보드를 로컬에서 확인할 수 있도록 해 줍니다.

사용 예시::

    python serve.py --port 8000
    python serve.py --host 0.0.0.0 --port 8080 --open-browser

`--port 0`을 지정하면 운영 체제가 사용 가능한 임의의 포트를 할당합니다.
"""

from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import sys
import threading
import webbrowser
from functools import partial


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="효율적 프런티어 대시보드용 정적 웹 서버")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"서버 바인딩 호스트 (기본값: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="서버 포트 (0 지정 시 사용 가능한 포트를 자동 배정)",
    )
    parser.add_argument(
        "--docs",
        default=DOCS_DIR,
        help="서빙할 문서 디렉터리 경로 (기본값: 저장소의 docs/)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="서버가 시작되면 기본 브라우저에서 대시보드 자동 열기",
    )
    return parser.parse_args(argv)


def _resolve_directory(path: str) -> str:
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        raise FileNotFoundError(f"문서 디렉터리를 찾을 수 없습니다: {abs_path}")
    return abs_path


def _format_url(host: str, port: int) -> str:
    host_part = host if host not in {"0.0.0.0", "::"} else "127.0.0.1"
    return f"http://{host_part}:{port}/"


def serve(host: str, port: int, docs_path: str, auto_open: bool) -> None:
    docs_directory = _resolve_directory(docs_path)
    handler_factory = partial(http.server.SimpleHTTPRequestHandler, directory=docs_directory)

    with contextlib.closing(
        http.server.ThreadingHTTPServer((host, port), handler_factory)
    ) as httpd:
        actual_host, actual_port = httpd.server_address
        url = _format_url(actual_host, actual_port)
        print("=" * 72)
        print("효율적 프런티어 대시보드를 서빙합니다.")
        print(f"문서 디렉터리 : {docs_directory}")
        print(f"접속 URL      : {url}")
        print("서버를 중지하려면 Ctrl+C를 누르세요.")
        print("=" * 72)

        if auto_open:
            threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다…")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        serve(args.host, args.port, args.docs, args.open_browser)
    except OSError as exc:  # 포트 충돌 등 소켓 오류 처리
        print(f"[오류] 서버를 시작하지 못했습니다: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"[오류] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
