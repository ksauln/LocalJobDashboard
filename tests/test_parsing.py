from src.tools.parsing import strip_html


def test_strip_html_basic():
    html = "<div>Hello <b>World</b><br/>New line</div>"
    assert strip_html(html) == "Hello World New line"
