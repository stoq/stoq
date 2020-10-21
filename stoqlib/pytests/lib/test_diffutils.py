from stoqlib.lib.diffutils import diff_strings


def test_diff_strings():
    assert diff_strings("foo", "foo") == ""
    assert diff_strings("foo", "bar")
