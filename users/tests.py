def is_superuser_or_vendor(user):
    return user.is_superuser or user.profile.vendor
