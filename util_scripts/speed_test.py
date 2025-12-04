import orjson
import ormsgpack
import time

for i in range(39):
    start = time.time()
    with open(f'..\\Barrels\\{i}.msgpack', 'rb') as f:
        data_msgpack = ormsgpack.unpackb(f.read())
    end = time.time()
    print(f"Time taken to read {i}.msgpack:", end - start)
    start = time.time()
    with open(f'..\\Barrels\\{i}.json', 'rb') as f:
        data_json = orjson.loads(f.read())
    end = time.time()
    print(f"Time taken to read {i}.json:", end - start)
    if data_msgpack != data_json:
        print(f"Difference found in {i}")
    else:
        print(f"barrel_{i} matches perfectly")