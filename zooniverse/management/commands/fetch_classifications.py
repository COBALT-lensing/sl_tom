import numpy

from django.core.management.base import BaseCommand

from zooniverse.data_import import (
    generate_classification_export,
    import_classifications,
)


class Command(BaseCommand):
    help = (
        "Imports new Zooniverse classifications, starting after the last one imported"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=numpy.inf,
            help="Limit the number of classifications imported",
        )
        parser.add_argument(
            "--generate",
            help="Generate a new classifications export and wait for it before importing",
            action="store_true",
        )

    def handle(self, *args, **options):
        if options["generate"]:
            generate_classification_export(wait=True)
        imported = import_classifications(limit=options["limit"])
        print(f"Imported {imported} classifications")
