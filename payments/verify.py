def verify_payments():
    import requests, json, datetime
    from .models import Invoice
    from django.utils import timezone
    invoices = Invoice.objects.filter(timestamp__gte=timezone.now() - datetime.timedelta(hours=1), completed=False).order_by('-timestamp')
    for invoice in invoices:
        res = False
        if invoice.processor == 'paypal':
            from payments.paypal import get_payment_status
            res = get_payment_status(invoice.number)
        elif invoice.processor == 'square':
            from payments.square import verify_payment
            if verify_payment(invoice.number):
                res = True
                print('Payment verified')
        if res:
            print('Updating payment')
            user = invoice.user
            from django.contrib.auth.models import User
            from django.conf import settings
            from feed.models import Post
            from payments.cart import get_cart_cost
            from django.http import HttpResponse
            product = invoice.product
            price = invoice.price
#            if product == 'cart' and (get_cart_cost(invoice.cart) if invoice.cart else 0) != int(price): return
#            if product == 'post' and Post.objects.filter(uuid=invoice.pid).first().price != str(price): return
#            if product == 'membership' and invoice.vendor.vendor_profile.subscription_fee != price: return
            vendor = invoice.vendor
            from payments.cart import process_cart_purchase
            if invoice.product == 'cart':
                process_cart_purchase(user, invoice.cart)
            if invoice.product == 'post':
                from feed.models import Post
                post = Post.objects.get(author=vendor, id=invoice.pid)
                if not post.paid_file:
                    post.recipient = user
                    post.save()
                    from feed.email import send_photo_email
                    send_photo_email(user, post)
                else:
                    from feed.email import send_photo_email
                    send_photo_email(user, post)
                    post.paid_users.add(user)
                    post.save()
            if invoice.product == 'surrogacy':
                mother = vendor
                from users.tfa import send_user_text
                send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
                from payments.surrogacy import save_and_send_agreement
                save_and_send_agreement(mother, user)
            if invoice.product == 'webdev':
                from payments.models import PurchasedProduct
                from users.tfa import send_user_text
                PurchasedProduct.objects.create(user=user, description=product_desc, price=int(price), paid=True)
                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased a web dev product for ${} - "{}"'.format(user.username, price_dev[product], product_desc))
            if invoice.product == 'idscan':
                user.profile.idscan_plan = int(price) * 2
                user.profile.idscan_active = True
                user.profile.idscan_used = 0
                user.profile.save()
                user.save()
                from users.tfa import send_user_text
                send_user_text(User.objects.get(id=settings.MY_ID), '@{} has purchased an ID scanner subscription product for ${}'.format(user.username, price_scans[plan]))
            if invoice.product == 'membership':
                user.profile.subscriptions.add(vendor)
                user.profile.save()
                from payments.models import Subscription
                if not Subscription.objects.filter(model=vendor, user=user, active=True).last(): Subscription.objects.create(model=vendor, user=user, active=True)
            invoice.completed = True
            invoice.save()
