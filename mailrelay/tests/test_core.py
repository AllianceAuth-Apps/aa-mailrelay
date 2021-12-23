from django.test import TestCase

from ..core import chunks_by_lines, eve_xml_to_discord_markup


class TestXmlToMarkup(TestCase):
    def test_should_replace_line_breaks(self):
        # given
        xml_doc = (
            '<font size="13" color="#ff999999">alpha<br>bravo<br><br>charlie</font>'
        )
        # when
        result = eve_xml_to_discord_markup(xml_doc)
        # then
        self.assertEqual(result, "alpha\nbravo\n\ncharlie")


class TestChunkLines(TestCase):
    def test_should_produce_chunks(self):
        # given
        input = "abcdef\nghijklmnopq\nrstuvwxyz"
        # when
        result = chunks_by_lines(input, 20)
        # then
        self.assertListEqual(result, ["abcdef\nghijklmnopq\n", "rstuvwxyz"])
