"""
Объяснение:
Синхронная версия (sync_main) выполняет сетевые запросы последовательно с помощью библиотеки `requests`:
каждый следующий запрос отправляется только после того, как полностью завершился предыдущий. 
Из-за этого общее время работы складывается из суммы задержек всех 20 запросов.

Асинхронная версия (fast_main) отправляет все запросы конкурентно (параллельно в рамках одного потока) 
с помощью `httpx.AsyncClient` и `asyncio.gather`. Цикл событий (event loop) не ждет завершения 
каждого отдельного запроса, а отправляет их пачкой, что драматически сокращает общее время выполнения.

Время выполнения:
- Синхронный вариант (sync): 15.73s
- Асинхронный вариант (async): 2.28s
"""

import asyncio
import time

import httpx
import requests

# 20 разных картинок (у каждой свой номер в адресе) — ответы достаточно
# «тяжёлые», чтобы разница между sync и async была хорошо видна
URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

def sync_main():
    for url in URLS:
        requests.get(url)  # по очереди, время складывается

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code

async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("sync ", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))
