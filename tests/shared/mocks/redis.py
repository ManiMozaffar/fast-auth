class RedisMock:
    database = {}

    async def get(self, name):
        return RedisMock.database.get(str(name), None)

    async def set(self, name, value, ex):
        RedisMock.database[str(name)] = value
        return True

    async def ttl(self, name):
        return 100

    async def delete(self, name):
        RedisMock.database.pop(str(name), None)
