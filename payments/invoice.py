def generate_invoice(vendor, user, price, description):
    import random
    from payments.models import Invoice
    from users.email import send_html_email
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.urls import reverse
    invoice = Invoice.objects.create(vendor=vendor, user=user, price=price, product="invoice", cart=description, pid=random.randrange(111111,999999))
    html_email = render_to_string('payments/invoice.html', {
        'pay_url': settings.BASE_URL + reverse('payments:pay-invoice') + '?pid={}'.format(invoice.pid),
        'user': user,
        'vendor': vendor,
        'invoice': invoice,
        'description': description,
        'site_name': settings.SITE_NAME
    })
    send_html_email(user, 'Your invoice from {}'.format(settings.SITE_NAME), html_email)

def process_invoice(invoice):
    import random
    from payments.models import Invoice
    from users.email import send_html_email
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.urls import reverse
    user = invoice.user
    vendor = invoice.vendor
    description = invoice.description
    html_email = render_to_string('payments/invoice_paid.html', {
        'user': user,
        'vendor': vendor,
        'invoice': invoice,
        'description': description,
        'site_name': settings.SITE_NAME
    })
    send_html_email(user, 'Invoice for {} (@{}) has been paid'.format(user.email, user.username), html_email)
