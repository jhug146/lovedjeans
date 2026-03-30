from django.db.models import F
from . import models

NO_RECORD = ("session/", "_cart", "upload_", "lookup_", "get_", "delete_", "_payment", "analytics/", "favicon", "jsonws", "_ignition")

def analytics(get_response):

    def middleware(request):
        response = get_response(request)

        page = request.path

        for value in NO_RECORD:
            if value in page:
                return response

        models.Views.objects.update_or_create(
            name=page,
            defaults={'views': F('views') + 1},
            create_defaults={'views': 1}
        )

        session_id = request.COOKIES.get("sessionid")
        if session_id:
            models.Sessions.objects.get_or_create(session_id=session_id)

        return response

    return middleware