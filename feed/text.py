def is_safe_text(text):
    from better_profanity import profanity
    return not profanity.contains_profanity(text)

def censor(text):
    from better_profanity import profanity
    return profanity.censor(text)

