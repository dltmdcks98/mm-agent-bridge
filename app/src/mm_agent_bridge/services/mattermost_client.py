import httpx


def post_worker_result(response_url: str, summary: str) -> None:
    payload = {"text": summary}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(response_url, json=payload)
        response.raise_for_status()
