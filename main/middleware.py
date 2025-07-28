from . import models
from datetime import date

NO_RECORD = ("session/", "_cart", "upload_", "lookup_", "get_", "delete_", "_payment", "analytics/", "favicon", "jsonws", "_ignition")

def analytics(get_response):

    def middleware(request):
        response = get_response(request)
        
        #Page views counter
        page = request.path
        
        #Check if page is non-user page
        for value in NO_RECORD:
            if value in page:
                return response

        try:
            page_model = models.Views.objects.get(name=page)
            page_model.views += 1
            page_model.save()
        except models.Views.DoesNotExist:
            page_model = models.Views.objects.create(name=page, views=1)
            page_model.save()


        #Session counter
        session_id = request.COOKIES.get("sessionid")
        try:
            models.Sessions.objects.get(session_id=session_id)
        except:
            if session_id:
                models.Sessions.objects.create(session_id=session_id)

        return response

    return middleware