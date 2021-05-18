#!/usr/bin/env python3
from collections import OrderedDict

# See for example: https://www.geeksforgeeks.org/lru-cache-in-python-using-ordereddict/

class LruCache:
    # initialising capacity
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def add_and_check_exist(self, key: str) -> bool:
        if key not in self.cache:
            self.cache[key] = True
            self.cache.move_to_end(key)

            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

            return False
        else:
            self.cache.move_to_end(key)
            return True

