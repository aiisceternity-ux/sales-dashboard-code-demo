#!/usr/bin/env python3
"""売上ダッシュボード用のローカルサーバー。

同じフォルダにある「同じ列構成のCSV」(日付,商品名,カテゴリ,地域,数量,単価,売上金額)を
一覧・選択できるようにし、ダッシュボードHTMLに生データを渡す。

使い方:
    python3 server.py
    -> http://127.0.0.1:8420/ をブラウザで開く
"""
import http.server
import socketserver
import os
import glob
import json
import urllib.parse

PORT = 8420
DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.BaseHTTPRequestHandler):
    def _send_bytes(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status=200):
        self._send_bytes(
            json.dumps(data, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _send_text(self, text, content_type, status=200):
        self._send_bytes(text.encode("utf-8"), content_type, status)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            fp = os.path.join(DIR, "dashboard.html")
            with open(fp, encoding="utf-8") as f:
                self._send_text(f.read(), "text/html; charset=utf-8")
            return

        if path == "/api/files":
            files = sorted(
                os.path.basename(p) for p in glob.glob(os.path.join(DIR, "*.csv"))
            )
            self._send_json({"files": files})
            return

        if path == "/api/csv":
            name = (qs.get("file") or [None])[0]
            if not name or "/" in name or "\\" in name or not name.endswith(".csv"):
                self._send_json({"error": "invalid file"}, 400)
                return
            fp = os.path.join(DIR, name)
            if not os.path.isfile(fp):
                self._send_json({"error": "not found"}, 404)
                return
            with open(fp, encoding="utf-8") as f:
                self._send_text(f.read(), "text/csv; charset=utf-8")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    os.chdir(DIR)
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"売上ダッシュボード: http://127.0.0.1:{PORT}/ (Ctrl+C で終了)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止しました")


if __name__ == "__main__":
    main()
