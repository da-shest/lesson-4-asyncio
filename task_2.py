import asyncio
import time

import httpx

# 20 разных картинок (у каждой свой номер в адресе) — ответы достаточно
# «тяжёлые», чтобы разница между sync и async была хорошо видна
URLS = [f"https://jsonplaceholder.typicode.com/photos/{i}" for i in range(1, 21)] + \
    ["https://no-such-site.invalid", "https://httpbin.org/delay/10"]

RETRIES = 3
TIMEOUT = 9

def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    for attempt in range(RETRIES):
        try:
            response = await client.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.status_code
        except (httpx.TimeoutException, httpx.HTTPError) as error:
            if attempt == RETRIES - 1:
                raise
            await asyncio.sleep(2 ** attempt)

async def robust_main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        responses = await asyncio.gather(
            *(robust_fetch(client, url) for url in URLS),
            return_exceptions=True
        )
        results = [r for r in responses if not isinstance(r, Exception)]
        errors = [r for r in responses if isinstance(r, Exception)]
        
        print(f"Successful results len: {len(results)}")
        print(f"Errors len: {len(errors)}")

        # for err in errors[:5]:  # покажем первые 5 ошибок
        #     print(type(err), err)

        return results, errors

if __name__ == "__main__":
    timed("async", lambda: asyncio.run(robust_main()))
