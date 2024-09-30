from django.conf import settings

from panoptes_client import Panoptes

if (
    settings.ZOONIVERSE_CLIENT_ID
    and settings.ZOONIVERSE_CLIENT_SECRET
    and not Panoptes.client().logged_in()
):
    Panoptes.connect(
        client_id=settings.ZOONIVERSE_CLIENT_ID,
        client_secret=settings.ZOONIVERSE_CLIENT_SECRET,
    )
