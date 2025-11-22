from gui import tab_config
from models.options_data import CHARACTER_OPTIONS


def test_tab_names_unique_and_ordered():
    tab_names = tab_config.all_tab_names()

    assert len(tab_names) == len(set(tab_names))
    assert tab_names[: len(tab_config.DEFAULT_TABS)] == [
        name for name, _, _ in tab_config.DEFAULT_TABS
    ]
    assert tab_names[-len(tab_config.STATIC_TABS) :] == list(tab_config.STATIC_TABS)


def test_tab_headers_align_with_options_data():
    configured_headers = {header for _, header, _ in tab_config.DEFAULT_TABS}

    assert configured_headers.issubset(set(CHARACTER_OPTIONS))
