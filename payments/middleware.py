import traceback

def payments_middleware(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        response = None
        try:
            response = get_response(request)
        except:
            print(traceback.format_exc())
        return response
    return middleware
