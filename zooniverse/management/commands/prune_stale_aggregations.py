from django.core.management.base import BaseCommand

from tqdm import tqdm

from zooniverse.models import ZooniverseTargetReduction


class Command(BaseCommand):
    help = "Removes target reductions for targets with new classifications"

    def handle(self, *args, **options):
        for tr in tqdm(ZooniverseTargetReduction.objects.all()):
            if tr.target.classifications().filter(created__gt=tr.created).count() > 0:
                tr.delete()
