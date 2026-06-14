import sys
import contextlib
import io
import time
from tqdm import tqdm

class MyStream(io.StringIO):
    def write(self, s):
        if s.strip():
            print(f"CAPTURED: {repr(s)}")
        return super().write(s)

stream = MyStream()
with contextlib.redirect_stderr(stream):
    for i in tqdm(range(5)):
        time.sleep(0.1)
