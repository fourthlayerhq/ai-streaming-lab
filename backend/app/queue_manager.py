import asyncio

class ConcurrencyManager:
    def __init__(self):
        self.max_slots = 3
        self.active_slots = 0
        self._condition = asyncio.Condition()
        
    async def acquire(self):
        async with self._condition:
            while self.active_slots >= self.max_slots:
                await self._condition.wait()
            self.active_slots += 1

    async def __aenter__(self):
        await self.acquire()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._condition:
            self.active_slots -= 1
            self._condition.notify_all()
            
    async def set_slots(self, new_slots: int):
        async with self._condition:
            self.max_slots = new_slots
            self._condition.notify_all()

stream_semaphore = ConcurrencyManager()