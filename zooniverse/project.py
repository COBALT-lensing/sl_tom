import datetime
import json
import logging

from csv import DictReader

from dateutil.parser import parse as date_parse

from django.conf import settings

from client import project, workflow
from models import ZooniverseClassification, ZooniverseSubject

logger = logging.getLogger(__name__)


def generate_subject_export():
    return project.generate_export("subjects")


def generate_classification_export():
    return workflow.generate_export("classifications")


def get_subject_export():
    return project.get_export("subjects").content.decode("utf-8")


def get_classification_export():
    return workflow.get_export("classifications").content.decode("utf-8")


def import_classifications():
    existing_classifications = ZooniverseClassification.objects.all().values_list(
        "classification_id", flat=True
    )
    existing_subjects = ZooniverseSubject.objects.all().values_list(
        "subject_id", flat=True
    )
    for c in DictReader(get_classification_export()):
        classification_id = int(c["classification_id"])
        subject_id = int(c["subject_id"])
        user_id = int(c["user_id"])

        if classification_id in existing_classifications:
            continue

        if subject_id not in existing_subjects:
            logger.warning(
                f"Skipping classification {classification_id} for unknown subject {subject_id}"
            )
            continue

        subject = ZooniverseSubject.objects.get(subject_id=subject_id)

        annotation = json.loads(c["annotation"])
        timestamp = date_parse(c["created_at"])

        ZooniverseClassification.objects.create(
            classification_id=classification_id,
            subject=subject,
            user_id=user_id,
            timestamp=timestamp,
            annotation=annotation,
        )
