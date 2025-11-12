def get_language_selector():
    from translate.languages import SELECTOR_LANGUAGES
    options = [['', 'Default to browser language']]
    for key, value in SELECTOR_LANGUAGES.items():
        options += [[key, value]]
    return options
