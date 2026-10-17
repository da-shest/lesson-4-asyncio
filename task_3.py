import asyncio
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor
import httpx
import os

URLS = [f"https://jsonplaceholder.typicode.com/photos/{i}" for i in range(1, 21)]
RETRIES = 3
TIMEOUT = 9

def timed(label, fn, *args):
    """Запускает fn(*args) и печатает, сколько секунд она работала."""
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

def heavy(body: bytes) -> str:
    # body * 1000 раздувает данные, чтобы хеш считался заметно долго
    return hashlib.sha256(body * 1000).hexdigest()

async def ticker():
    # «пульс» event loop: если точки перестали печататься — loop заблокирован
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.1)

async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    for attempt in range(RETRIES):
        try:
            response = await client.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.content
        except (httpx.TimeoutException, httpx.HTTPError) as error:
            if attempt == RETRIES - 1:
                raise
            await asyncio.sleep(2 ** attempt)

async def cpu_main():
    # 1) запусти ticker фоновой задачей: asyncio.create_task(ticker())
    # 2) скачай ответы и посчитай heavy «в лоб» — точки замрут
    # 3) посчитай heavy через loop.run_in_executor + ProcessPoolExecutor —
    #    точки бегут
    # 4) в конце отмени ticker через .cancel()
    background_task = asyncio.create_task(ticker())
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            print('Скачивание')
            responses = await asyncio.gather(
                *(robust_fetch(client, url) for url in URLS),
                return_exceptions=True
            )
            responses = [r for r in responses if not isinstance(r, Exception)]
            print(f'\nКоличество успешных запросов: {len(responses)}')
            print('\nСинхронный расчет heavy')
            for response in responses:
                heavy(response)
            print('\nАсинхронный расчет heavy')
            loop = asyncio.get_running_loop()
            hashes_coroutines = []
            for response in responses:
                hashes_coroutines.append(loop.run_in_executor(executor, heavy, response))
            await asyncio.gather(*hashes_coroutines)

    print('\nЗавершение работы')
    background_task.cancel()




if __name__ == "__main__":
    timed("cpu  ", lambda: asyncio.run(cpu_main()))
