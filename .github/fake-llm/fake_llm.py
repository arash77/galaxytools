"""TEST ONLY: fake OpenAI-compatible LLM for the nested-tool-dir workflow test.

Feedback flow: one write_file that fixes the two planted typos in the imagej2
threshold tool, then "Done.". Anything else (review): "Done.".
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

FILE = "imagej2_adjust_threshold_binary.xml"
SRC = "tools/image_processing/imagej2/" + FILE
done = set()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        tools = {t["function"]["name"] for t in req.get("tools", [])}
        first_user = str(next((m["content"] for m in req["messages"] if m["role"] == "user"), ""))
        msg, finish = {"role": "assistant", "content": "Done."}, "stop"
        if "write_file" in tools and "addressing feedback" in first_user and "fix" not in done:
            done.add("fix")
            xml = open(SRC).read().replace("imgaes", "images").replace("backgorund", "background")
            msg = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_fix", "type": "function",
                "function": {"name": "write_file", "arguments": json.dumps({"path": FILE, "content": xml})}}]}
            finish = "tool_calls"
        print("request: tools=%d -> %s" % (len(tools), finish), flush=True)
        data = json.dumps({"id": "fake", "object": "chat.completion", "model": "stub",
                           "choices": [{"index": 0, "finish_reason": finish, "message": msg}],
                           "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
