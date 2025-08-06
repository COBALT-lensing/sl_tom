import json
import math
import numpy
import tarfile

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from tqdm import tqdm

from zooniverse.models import ZooniverseSurvey, ZooniverseTarget, ZooniverseSubject


def nan_filter(x):
    if isinstance(x, str) or isinstance(x, list):
        return x
    if math.isnan(x):
        return ""
    return x


class Command(BaseCommand):
    help = "Imports TESS subjects from JSON metadata (for subjects created before SL-TOM existed)"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)
        parser.add_argument(
            "--limit",
            type=int,
            default=numpy.inf,
            help="Limit the number of subjects imported",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file_path"])
        if not file_path.exists():
            raise CommandError(f'Metadata file {options["file_path"]} not found')

        tess_survey, _ = ZooniverseSurvey.objects.get_or_create(name="TESS")

        with tarfile.open(file_path, "r") as tar:
            i = 0
            for tar_member in tqdm(tar):
                if not tar_member.name.endswith(".json"):
                    continue
                if "/._" in tar_member.name:
                    # Skip resource forks
                    continue

                metadata = json.load(tar.extractfile(tar_member))

                for subject_id, meta in metadata.items():
                    del meta["survey_name"]
                    meta = {k: nan_filter(v) for k, v in meta.items()}

                    target, _ = ZooniverseTarget.objects.get_or_create(
                        survey=tess_survey, identifier=meta["target"]
                    )
                    ZooniverseSubject.objects.get_or_create(
                        subject_id=subject_id,
                        target=target,
                        sequence=meta.pop("sector"),
                        data_url=meta.pop("data_url"),
                        metadata=meta,
                    )
                i += 1
                if i >= options["limit"]:
                    break
