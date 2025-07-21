from django.contrib.auth.tokens import PasswordResetTokenGenerator
class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        import six
        return (
            six.text_type(user.pk) + six.text_type(timestamp)
        )
account_activation_token = TokenGenerator()
unsubscribe_token = TokenGenerator()
