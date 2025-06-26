from django import forms

import random

def get_random_color():
    # Generate a random integer between 0 and 16,777,215 (0xFFFFFF)
    # This covers all possible 24-bit RGB color values.
    random_number = random.randint(0, 0xFFFFFF)
    # Format the integer as a 6-digit hexadecimal string, padded with leading zeros
    # The '#{:06x}' format specifier ensures a '#' prefix and 6 lowercase hex digits.
    hex_color = '#{:06x}'.format(random_number)
    return hex_color

class LinksForm(forms.Form):
    def __init__(self, *args, **kwargs):
        from translate.translate import translate
        from feed.middleware import get_current_request
        r = get_current_request()
        links_data = kwargs.pop('links', None)
        super(LinksForm, self).__init__(*args, **kwargs)
        ind = 0
        for index, item in enumerate(links_data):
            field_name = 'link{}'.format(index)
            self.fields[field_name] = forms.CharField(label=translate(r, 'Link', src='en') + ' {}'.format(index), required=False, initial=item.url, widget=forms.TextInput(attrs={'autocorrect': 'off', 'spellcheck': 'false', 'autocapitalize': 'none'}))
            field_name = 'description{}'.format(index)
            self.fields[field_name] = forms.CharField(label=translate(r, 'Description', src='en') + ' {}'.format(index), required=False, initial=item.description)
            field_name = 'color{}'.format(index)
            self.fields[field_name] = forms.CharField(label=translate(r, 'Color', src='en') + ' {}'.format(index), widget=forms.TextInput(attrs={'type': 'color'}), initial=item.color, required=False)
            ind = index
        index = ind + 1
        field_name = 'link{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Link', src='en') + ' {}'.format(index), required=False, initial='', widget=forms.TextInput(attrs={'autocorrect': 'off', 'spellcheck': 'false', 'autocapitalize': 'none'}))
        field_name = 'description{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Description', src='en') + ' {}'.format(index), required=False)
        field_name = 'color{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Color', src='en') + ' {}'.format(index), widget=forms.TextInput(attrs={'type': 'color'}), initial=get_random_color(), required=False)
        index = index + 1
        field_name = 'link{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Link', src='en') + ' {}'.format(index), required=False, initial='', widget=forms.TextInput(attrs={'autocorrect': 'off', 'spellcheck': 'false', 'autocapitalize': 'none'}))
        field_name = 'description{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Description', src='en') + ' {}'.format(index), required=False)
        field_name = 'color{}'.format(index)
        self.fields[field_name] = forms.CharField(label=translate(r, 'Color', src='en') + ' {}'.format(index), widget=forms.TextInput(attrs={'type': 'color'}), initial=get_random_color(), required=False)
