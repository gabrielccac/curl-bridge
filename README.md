# curl-bridge

Tiny API that fetches a URL using a browser-impersonated `curl_cffi` request
and returns the upstream response as-is (status, headers, body).

    pip install -r requirements.txt
    uvicorn app.main:app --port 8000

    curl "localhost:8000/fetch?url=https://example.com"

- GET only; client headers are forwarded. URL-encode the `url` value if it has its own query string (`curl -G --data-urlencode "url=..."`).
- `impersonate` query param (default `chrome`, or env `IMPERSONATE`) picks the browser profile.
- `REQUEST_TIMEOUT` env sets the upstream timeout (default 30s). Redirects are passed through, not followed.
- Upstream connection errors return `502`; invalid URLs return `400`.
