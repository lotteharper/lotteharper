from django.conf import settings

def barcode_middleware(get_response):
    def middleware(request):
        response = None
        import traceback
        try:
#            if request.user.is_authenticated:
#                if (DocumentScan.objects.filter(user=request.user, verified=True, side=True).count() == 0 or DocumentScan.objects.filter(user=request.user, verified=True, side=False).count() == 0) and (request.user.profile.id_back_scanned or request.user.profile.id_front_scanned) and not request.user.id == settings.MODERATOR_USER_ID: # comment last and not
#                    request.user.profile.id_front_scanned = False
#                    request.user.profile.id_back_scanned = False
#                    request.user.profile.save()
#                if IdentityDocument.objects.filter(user=request.user, verified=True).count() == 0 and request.user.profile.identity_verified and not request.user.id == settings.MODERATOR_USER_ID: # comment last and not
#                    request.user.profile.identity_verified = False
#                    request.user.profile.save()
            response = get_response(request)
        except:
            print(traceback.format_exc())
            response = get_response(request)
        return response
    return middleware
