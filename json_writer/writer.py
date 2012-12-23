try:
    from __pypy__.builders import StringBuilder
except ImportError:
    StringBuilder = None
from abc import ABCMeta, abstractmethod
from io import BytesIO
import math


class _ArrayElement(object):
    def __init__(self, writer):
        self.writer = writer
        self.ctx = -1

    def __enter__(self):
        self.writer._starting_element()
        self.ctx = self.writer.ctx
        self.writer.ctx = self.writer.ARRAY_START_CTX
        self.writer._write(b"[")

    def __exit__(self, *exc_info):
        self.writer._write(b"]")
        self.writer.ctx = self.ctx


class _ObjectElement(object):
    def __init__(self, writer):
        self.writer = writer
        self.ctx = -1

    def __enter__(self):
        self.writer._starting_element()
        self.ctx = self.writer.ctx
        self.writer.ctx = self.writer.OBJECT_START_KEY_CTX
        self.writer._write(b"{")

    def __exit__(self, *exc_info):
        self.writer._write(b"}")
        self.writer.ctx = self.ctx


class BaseJSONWriter(object):
    __metaclass__ = ABCMeta

    START_CTX = 0
    ARRAY_START_CTX = 1
    ARRAY_CTX = 2
    OBJECT_START_KEY_CTX = 3
    OBJECT_KEY_CTX = 4

    def __init__(self):
        if not self.is_available():
            raise NotImplementedError("%s is not available on this platform" %
                type(self))
        self.ctx = self.START_CTX

    @abstractmethod
    def _write(self, s):
        raise NotImplementedError

    @abstractmethod
    def build(self):
        raise NotImplementedError

    @classmethod
    def is_available(cls):
        raise NotImplementedError

    def _starting_element(self):
        if self.ctx == self.ARRAY_CTX:
            self._write(b",")
        elif self.ctx == self.ARRAY_START_CTX:
            self.ctx = self.ARRAY_CTX

    def array(self):
        return _ArrayElement(self)

    def object(self):
        return _ObjectElement(self)

    def _write_bytes(self, s):
        start = 0
        i = 0
        while 0 <= i < len(s):
            c = ord(s[i])
            if not (c >= ord(" ") and c <= ord("~") and c != ord("\\") and c != ord('"')):
                self._write(s[start:i])
                start = i + 1
                self._write(b"\\")
                if c == ord("\\") or c == ord('"'):
                    self._write(c)
                elif c == ord("\b"):
                    self._write(b"b")
                elif c == ord("\f"):
                    self._write(b"f")
                elif c == ord("\n"):
                    self._write(b"n")
                elif c == ord("\r"):
                    self._write(b"r")
                elif c == ord("\t"):
                    self._write(b"t")
                else:
                    if c >= 0x10000:
                        v = c - 0x10000
                        c = 0xD800 | ((v >> 10) & 0x3FF)
                        self._write(b"u")
                        self._write("0123456789abcdef"[(c >> 12) & 0xF])
                        self._write("0123456789abcdef"[(c >> 8) & 0xF])
                        self._write("0123456789abcdef"[(c >> 4) & 0xF])
                        self._write("0123456789abcdef"[c & 0xF])
                        c = 0xDC00 | (v & 0x3FF)
                        self._write("\\")
                    self._write(b"u")
                    self._write("0123456789abcdef"[(c >> 12) & 0xF])
                    self._write("0123456789abcdef"[(c >> 8) & 0xF])
                    self._write("0123456789abcdef"[(c >> 4) & 0xF])
                    self._write("0123456789abcdef"[c & 0xF])
            i += 1
        self._write(s[start:])

    def write(self, v):
        if self.ctx == self.START_CTX:
            raise TypeError("Top level JSON structure must be object or array")
        self._starting_element()
        if v is None:
            self._write(b"null")
        elif isinstance(v, int):
            self._write(bytes(str(v)))
        elif isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Out of range float values are not JSON "
                    "compliant: %r" % v)
            self._write(bytes(repr(v)))
        elif isinstance(v, bytes):
            self._write(b'"')
            self._write_bytes(v)
            self._write(b'"')
        else:
            raise TypeError("Don't recognize object of type %s" % type(v))

    def write_key(self, s):
        if (self.ctx != self.OBJECT_KEY_CTX and
            self.ctx != self.OBJECT_START_KEY_CTX):
            raise TypeError("Not at object key position")
        if self.ctx == self.OBJECT_KEY_CTX:
            self._write(b",")
        self._write(b'"')
        if isinstance(s, bytes):
            self._write_bytes(s)
        elif isinstance(s, unicode):
            self._write_unicode(s)
        else:
            raise TypeError("key must be either bytes or unicode")
        self._write(b'"')
        self._write(b":")
        self.ctx = self.OBJECT_KEY_CTX


class PyPyStringBuilderWriter(BaseJSONWriter):
    def __init__(self):
        super(PyPyStringBuilderWriter, self).__init__()
        self._data = StringBuilder()

    @classmethod
    def is_available(cls):
        return StringBuilder is not None

    def _write(self, s):
        self._data.append(s)

    def build(self):
        return self._data.build()


class BytesIOWriter(BaseJSONWriter):
    def __init__(self):
        super(BytesIOWriter, self).__init__()
        self._data = BytesIO()

    @classmethod
    def is_available(cls):
        return True

    def _write(self, s):
        self._data.write(s)

    def build(self):
        return self._data.getvalue()

if StringBuilder is not None:
    JSONWriter = PyPyStringBuilderWriter
else:
    JSONWriter = BytesIOWriter
