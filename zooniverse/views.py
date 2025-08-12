from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.contrib.auth.mixins import LoginRequiredMixin

from zooniverse.forms import TargetLookupForm
from django.shortcuts import redirect
from zooniverse.models import (
    ZooniverseTarget,
)


class ZooniverseTargetDetailView(LoginRequiredMixin, DetailView):
    model = ZooniverseTarget


class ZooniverseTargetListView(LoginRequiredMixin, ListView):
    model = ZooniverseTarget

    def render_to_response(self, context, **response_kwargs):
        queryset = context.get("object_list", self.get_queryset())
        if queryset.count() == 1:
            print(queryset)
            obj = list(queryset)[0]  # Calling .first() fails
            return redirect("zooniverse:zooniversetarget_detail", pk=obj.pk)
        return super().render_to_response(context, **response_kwargs)

    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(identifier__icontains=search) | queryset.filter(
                zooniversesubject__subject_id__icontains=search
            )
            queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_lookup_form"] = TargetLookupForm(
            initial={"search": self.request.GET.get("search", "")}
        )
        return context
