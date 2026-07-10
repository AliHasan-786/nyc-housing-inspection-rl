import json
from urllib.parse import parse_qs

import httpx

from nyc_housing_rl.data.client import SocrataClient


def test_client_paginates_until_short_page() -> None:
    observed_offsets: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = parse_qs(request.url.query.decode())
        offset = int(params["$offset"][0])
        observed_offsets.append(offset)
        rows = [{"id": str(i)} for i in range(offset, min(offset + 2, 5))]
        return httpx.Response(200, content=json.dumps(rows), request=request)

    with SocrataClient(page_size=2, transport=httpx.MockTransport(handler)) as client:
        pages = list(client.iter_pages("test-id", {"$order": "id"}))

    assert [len(page) for page in pages] == [2, 2, 1]
    assert observed_offsets == [0, 2, 4]
