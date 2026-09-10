import importlib.util
import io
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "schema_inventory_reader.py"
SPEC = importlib.util.spec_from_file_location("schema_inventory_reader", MODULE_PATH)
reader = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(reader)


class RecordingStream:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)
        self.requests = []

    def read(self, size=-1):
        self.requests.append(size)
        return self._stream.read(size)


class CsvHeaderReaderTests(unittest.TestCase):
    def test_sentinel_after_header_is_never_requested(self):
        source = RecordingStream(b"first,second\nSECRET_SENTINEL")
        columns, raw = reader.read_csv_header(source)
        self.assertEqual(columns, ["first", "second"])
        self.assertEqual(raw, b"first,second\n")
        self.assertEqual(source._stream.tell(), len(raw))
        self.assertEqual(set(source.requests), {1})

    def test_bom_crlf_and_quoted_column(self):
        source = RecordingStream(b'\xef\xbb\xbf"first,name",second\r\nSENTINEL')
        columns, raw = reader.read_csv_header(source)
        self.assertEqual(columns, ["first,name", "second"])
        self.assertTrue(raw.endswith(b"\r\n"))
        self.assertEqual(source._stream.tell(), len(raw))

    def test_rejects_unterminated_and_overlong_headers(self):
        with self.assertRaises(reader.SchemaReadError):
            reader.read_csv_header(RecordingStream(b"a,b"))
        with self.assertRaises(reader.SchemaReadError):
            reader.read_csv_header(RecordingStream(b"abcd\nSENTINEL"), max_bytes=3)

    def test_rejects_multiline_header_without_reading_second_line(self):
        source = RecordingStream(b'"first\ncontinued",second\nSENTINEL')
        with self.assertRaises(reader.SchemaReadError):
            reader.read_csv_header(source)
        self.assertEqual(source._stream.tell(), len(b'"first\n'))

    def test_json_schema_does_not_return_values(self):
        schema = reader.json_schema({"secret": "SENTINEL", "items": [1, None]})
        self.assertEqual(schema["$.secret"], ("string",))
        self.assertNotIn("SENTINEL", repr(schema))


if __name__ == "__main__":
    unittest.main()
