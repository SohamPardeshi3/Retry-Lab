from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RetryLab HTTP fault-injection proxy")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: loopback only)")
    parser.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    args = parser.parse_args()
    uvicorn.run("retrylab.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
