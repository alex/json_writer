import json_writer

import pytest


@pytest.fixture(params=[json_writer.BytesIOWriter, json_writer.PyPyStringBuilderWriter])
def writer(request):
    if not request.param.is_available():
        pytest.skip()
    return request.param()


class TestWriter(object):
    def test_empty_arary(self, writer):
        with writer.array():
            pass
        assert writer.build() == b"[]"

    def test_array(self, writer):
        with writer.array():
            with writer.array():
                pass
            with writer.array():
                pass
        assert writer.build() == b"[[],[]]"

    def test_number(self, writer):
        with writer.array():
            writer.write(2)
            writer.write(2.0)
        assert writer.build() == b"[2,2.0]"

    def test_none(self, writer):
        with writer.array():
            writer.write(None)
        assert writer.build() == b"[null]"

    def test_top_level_non_object_array(self, writer):
        with pytest.raises(TypeError):
            writer.write(None)

    def test_empty_object(self, writer):
        with writer.object():
            pass
        assert writer.build() == b"{}"

    def test_object(self, writer):
        with writer.object():
            writer.write_key("t")
            writer.write(None)
        assert writer.build() == b'{"t":null}'

    def test_multi_key_object(self, writer):
        with writer.object():
            writer.write_key("a")
            writer.write(123)

            writer.write_key("b")
            with writer.array():
                pass

            writer.write_key("c")
            writer.write(None)
        assert writer.build() == b'{"a":123,"b":[],"c":null}'

    def test_write_str(self, writer):
        with writer.array():
            writer.write("\b")
            writer.write("\f")
            writer.write("\n")
            writer.write("\r")
            writer.write("\t")
        assert writer.build() == b'["\\b","\\f","\\n","\\r","\\t"]'

    def test_non_key_object(self, writer):
        with pytest.raises(TypeError):
            with writer.object():
                writer.write(12)
        with pytest.raises(TypeError):
            with writer.object():
                writer.write_key("abc")
                writer.write(123)
                writer.write(456)
