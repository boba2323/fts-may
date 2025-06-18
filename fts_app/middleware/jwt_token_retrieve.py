

# https://docs.djangoproject.com/en/5.1/topics/http/middleware/#writing-your-own-middleware
# this is just simple middleware code from the docs 
class CustomTokenMiddleware:
    '''this custome middleware takes the access tokens from requests.session and passes it to request.META 
        (from tokenobtainserialiser)
        The middleware is done through before the request is sent to the view. Thus the view finds the access token
        and authorises the request. This is a temporary answer to a serverside issue. With proper frontend we
        wont need this we will add this to the settings middleware.
    '''
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        # we added this code 
        token = request.session.get('token')
        if token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'


        # Code to be executed for each request/response after
        # the view is called.
        response = self.get_response(request)
        return response