import random
import time

# buffer = [None] * 10

# for i in range(50):
#     print(buffer)

#     buffer.pop(0)
#     buffer.append(random.randint(0, 9))

#     time.sleep(0.5)

import collections

buffer = collections.deque(maxlen = 10)

for i in range(50):
    print(buffer)

    buffer.append(random.randint(0, 9))

    time.sleep(0.5)

print(buffer)