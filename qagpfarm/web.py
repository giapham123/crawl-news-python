import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from qagpfarm.qa import GPFarmQA


STATIC_DIR = Path(__file__).with_name("static")
MAX_HISTORY_MESSAGES = 12


class GPFarmWebHandler(BaseHTTPRequestHandler):
    assistant: GPFarmQA
    stream_answers = False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            path = "/index.html"

        file_path = (STATIC_DIR / path.lstrip("/")).resolve()
        if not self._is_static_path(file_path) or not file_path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_file(file_path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/ask":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            question = str(payload.get("question", "")).strip()
            history = self._clean_history(payload.get("history", []))
        except (json.JSONDecodeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if not question:
            self._send_json({"error": "Question is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            intent = self.assistant._classify_offline(question)
            routed_query = question
            if self.stream_answers:
                self._send_streamed_answer(intent, routed_query, history)
                return
            answer = self.assistant.answer_with_intent(intent, routed_query, history=history)
        except Exception as exc:
            self._send_json({"error": f"Could not answer right now: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"answer": answer})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Request body is required")
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def _clean_history(self, value: Any) -> List[Dict[str, str]]:
        if not isinstance(value, list):
            return []

        history: List[Dict[str, str]] = []
        for item in value[-MAX_HISTORY_MESSAGES:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                history.append({"role": role, "content": content.strip()})
        return history

    def _is_static_path(self, file_path: Path) -> bool:
        try:
            file_path.relative_to(STATIC_DIR.resolve())
            return True
        except ValueError:
            return False

    def _send_file(self, file_path: Path) -> None:
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_types.get(file_path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_streamed_answer(self, intent: str, query: str, history: List[Dict[str, str]]) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        for chunk in self.assistant.stream_answer_with_intent(intent, query, history=history):
            if not chunk:
                continue
            self.wfile.write(chunk.encode("utf-8"))
            self.wfile.flush()

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the GP Farm Q&A web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind, default 8000")
    parser.add_argument("--offline", action="store_true", help="Use local rule-based fallback instead of a model")
    parser.add_argument("--stream", action="store_true", help="Stream model answers to the browser")
    parser.add_argument("--model", default=None, help="Model name, default OPENAI_MODEL or qagpfarm.qa default")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    GPFarmWebHandler.assistant = GPFarmQA(model=args.model, base_url=args.base_url, use_llm=not args.offline)
    GPFarmWebHandler.stream_answers = args.stream
    server = ThreadingHTTPServer((args.host, args.port), GPFarmWebHandler)
    stream_label = " with streaming" if args.stream else ""
    print(f"GP Farm Q&A web UI running{stream_label} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GP Farm Q&A web UI.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
