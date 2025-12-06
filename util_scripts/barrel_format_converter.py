import orjson
import ormsgpack
import time

for i in range(72,79):
    with open(f'..\\Barrels\\{i}.json', 'rb') as f:
        data = orjson.loads(f.read())
    with open(f'..\\Barrels\\{i}.msgpack', 'wb') as f:
        f.write(ormsgpack.packb(data))
    print(f"Converted {i}.json to {i}.msgpack")