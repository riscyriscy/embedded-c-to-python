from array import array

import pytest

from frametool.crc16 import CHECK_VALUE, crc16


def test_check_value() -> None:
    assert crc16(b"123456789") == CHECK_VALUE


def test_accepts_any_bytes_like() -> None:
    assert crc16(bytearray(b"123456789")) == CHECK_VALUE
    assert crc16(memoryview(b"xx123456789")[2:]) == CHECK_VALUE


def test_reads_the_raw_bytes_of_any_buffer() -> None:
    items = array("h", [1, 2, 3])  # 6 bytes, and iterating gives 3 ints
    assert crc16(items) == crc16(items.tobytes())
    strided = memoryview(b"123456789")[::2]  # not contiguous: the raw bytes are not a run
    with pytest.raises(TypeError):
        crc16(strided)
