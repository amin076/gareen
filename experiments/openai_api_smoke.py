"""Minimal OpenAI Responses API connectivity smoke test for Gareen.

The API key is read only from OPENAI_API_KEY. The test makes one small request,
prints non-secret metadata and a short model response, and exits non-zero on failure.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.openai.com/v1/responses"
MODEL = os.environ.get("OPENAI_SMOKE_MODEL", "gpt-6-luna")


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is missing")
        return 2

    payload = {
        "model": MODEL,
        "input": (
            "You are a connectivity test for the Gareen mathematical discovery project. "
            "Reply with exactly: GAREEN_API_OK"
        ),
        "max_output_tokens": 32,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"OpenAI HTTP error: {exc.code}")
        print(error_body[:1000])
        return 1
    except Exception as exc:
        print(f"OpenAI request failed: {type(exc).__name__}: {exc}")
        return 1

    texts = []
    for item in body.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))
    output_text = "\n".join(texts).strip()

    print(f"OPENAI_API_CONNECTED model={body.get('model', MODEL)} response_id={body.get('id', 'unknown')}")
    print(f"MODEL_OUTPUT={output_text}")
    if "GAREEN_API_OK" not in output_text:
        print("Connection succeeded, but expected smoke-test marker was not returned.")
        return 3
    print("GAREEN_OPENAI_SMOKE=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
