class RedisMock:
    database = {}

    async def get(self, name):
        return RedisMock.database.get(name, None)

    async def set(self, name, value, ex):
        RedisMock.database[name] = value
        return True
