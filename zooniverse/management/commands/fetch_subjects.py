import numpy

from django.core.management.base import BaseCommand

from zooniverse.data_import import (
    generate_subject_export,
    import_subjects,
)


class Command(BaseCommand):
    help = "Imports new Zooniverse subjects and updates retirement for existing ones"

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
            generate_subject_export(wait=True)
        imported, updated = import_subjects(
            # TODO: Add target_identifier and sequence_identfier once existing subjects have these
            survey_identifier="survey_name",
            limit=options["limit"],
        )
        print(
            f"Imported {imported} classifications and updated {updated} classifications"
        )
