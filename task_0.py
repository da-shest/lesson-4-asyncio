"""
Объяснение:
Почему первоначальная реализация (slow_main) работала медленно?
В исходном коде вызов `await fetch(client, url)` происходил внутри обычного цикла `for`.
Из-за этого каждая следующая корутина запускалась только после того, как полностью 
завершалась предыдущая. Программа ждала ответ на первый запрос, затем отправляла второй, 
и так далее. Это приводило к последовательному (синхронному) выполнению запросов, 
несмотря на использование ключевых слов `async`/`await`.

В исправленном варианте (`fast_main`) используется функция `asyncio.gather`, которая 
собирает все корутины и запускает их параллельно (конкурентно) в цикле событий (event loop). 
Благодаря этому сетевые запросы отправляются одновременно и не блокируют друг друга.

Время выполнения:
- Последовательный вариант (slow): 5.51s
- Параллельный вариант (fast / asyncio.gather): 2.79s
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

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def slow_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in URLS:
            await fetch(client, url)  # <-- разобраться и починить

async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


# Запуск и замер:
timed("slow ", lambda: asyncio.run(slow_main()))
timed('fast ', lambda: asyncio.run(fast_main()))
