from django.test import TestCase

from ..core.xml_converter import eve_xml_to_discord_markup


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
