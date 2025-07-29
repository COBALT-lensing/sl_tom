from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.contrib.auth.mixins import LoginRequiredMixin

from zooniverse.models import (
    ZooniverseSubject,
    ZooniverseClassification,
    ZooniverseTarget,
)


class ZooniverseTargetDetailView(LoginRequiredMixin, DetailView):
    model = ZooniverseTarget


class ZooniverseTargetListView(LoginRequiredMixin, ListView):
    model = ZooniverseTarget
    paginate_by = 100
