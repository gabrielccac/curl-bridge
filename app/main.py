import os
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from fastapi import FastAPI, HTTPException, Query, Request, Response

IMPERSONATE = os.getenv("IMPERSONATE", "chrome")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))

# Headers that must not be forwarded from the client to the target, or copied
# back from the target to the client (the body is already decoded/re-framed).
HOP_BY_HOP = {
    "host", "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade",
    "content-length", "content-encoding",
}
REQUEST_ONLY_DROP = {"accept-encoding"}

app = FastAPI(title="curl-bridge")


@app.get("/fetch")
async def fetch(
    request: Request,
    url: str = Query(..., description="Target URL to request"),
    impersonate: str = Query(IMPERSONATE, description="curl_cffi browser profile"),
):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "url must be an absolute http(s) URL")

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP | REQUEST_ONLY_DROP
    }

    try:
        async with AsyncSession(impersonate=impersonate) as session:
            upstream = await session.request(
                "GET",
                url,
                headers=headers,
                timeout=TIMEOUT,
                allow_redirects=False,
            )
    except RequestException as exc:
        raise HTTPException(502, f"upstream request failed: {exc}")

    response = Response(
        content=upstream.content,
        status_code=upstream.status_code,
    )
    # Preserve repeated headers (e.g. Set-Cookie) by appending raw items.
    for key, value in upstream.headers.multi_items():
        if key.lower() not in HOP_BY_HOP:
            response.headers.append(key, value)
    return response
