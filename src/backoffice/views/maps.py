import logging
import json

from django.contrib import messages
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import GeometryCollection
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView
from leaflet.forms.widgets import LeafletWidget

from utils.widgets import IconPickerWidget
from ..mixins import OrgaTeamPermissionMixin
from camps.mixins import CampViewMixin
from maps.mixins import LayerViewMixin
from maps.models import Layer
from maps.models import ExternalLayer
from maps.models import Feature

logger = logging.getLogger("bornhack.%s" % __name__)


class MapsLayerView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    model = Layer
    template_name = "maps_layer_list_backoffice.html"
    context_object_name = "maps_layer_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['layers'] = Layer.objects.filter(Q(camp=self.camp) | Q(camp=None))
        context['externalLayers'] = ExternalLayer.objects.filter(Q(camp=self.camp) | Q(camp=None))
        return context


class MapsLayerImportView(LayerViewMixin, OrgaTeamPermissionMixin, View):
    model = Feature
    template_name = "maps_layer_import_backoffice.html"
    createdCount = 0
    updateCount = 0
    errorCount = 0

    def get(self, request, *args, **kwargs):
        context = dict()
        context['layer'] = Layer.objects.get(slug=kwargs['layer_slug'])
        return render(request, self.template_name, context)

    def post(self, request, camp_slug, layer_slug):
        geojson_data = request.POST.get('geojson_data')
        layer = get_object_or_404(
            Layer,
            slug=layer_slug,
        )
        try:
            geojson = json.loads(geojson_data)
        except json.JSONDecodeError:
            return render(request, 'maps_layer_import_backoffice.html', {'error': "Invalid GeoJSON data"})

        # Basic validation, you can add more checks
        if 'type' not in geojson or geojson['type'] != 'FeatureCollection':
            return render(request, 'maps_type_import_backoffice.html', {'error': "Invalid GeoJSON format"})

        if geojson['type'] == 'FeatureCollection':
            self.load_featureCollection(layer, geojson)

        if (self.createdCount > 0 or self.updateCount > 0):
            messages.success(self.request, "%i features created, %i features updated" % (self.createdCount, self.updateCount))
        if self.errorCount > 0:
            messages.error(self.request, "%i features with errors not imported" % (self.errorCount))
        return HttpResponseRedirect(reverse(
            "backoffice:maps_features_list",
            kwargs={"camp_slug": camp_slug, "layer_slug": self.layer.slug},
        ))

    def load_feature(self, layer, feature, props):
        try:
            geom = GeometryCollection(GEOSGeometry(json.dumps(feature['geometry'])))
        except (TypeError, AttributeError):
            logger.exception(f"Failed to GEOSGeometry: {feature}")
            self.errorCount += 1
            return
        created = self.createObject(props, layer, geom)
        if created:
            self.createdCount += 1
        else:
            self.updateCount += 1
        return

    def load_features(self, features):
        importFeatures = []
        for feature in features:
            try:
                f = GEOSGeometry(json.dumps(feature))
                importFeatures.append(f)
            except (TypeError, AttributeError):
                logger.exception(f"Failed to GEOSGeometry: {feature}")
                self.errorCount += 1
                return False
        return GeometryCollection(importFeatures)

    def load_featureCollection(self, layer, geojson):
        for feature in geojson['features']:
            if feature['geometry'] is None:
                self.createObject(feature['properties'], layer, GeometryCollection([]))
                continue
            if feature['geometry']['type'] == "GeometryCollection":
                geom = self.load_features(feature['geometry']['geometries'])
                if geom:
                    self.createObject(feature['properties'], layer, geom)
            elif feature['type'] == "Feature":
                self.load_feature(layer, feature, feature['properties'])
                continue

    def createObject(self, props, layer, geom):
        obj, created = Feature.objects.update_or_create(
            name=props['name'],
            description=props['description'],
            topic=props['topic'],
            processing=props['processing'],
            color=props['color'],
            layer=layer,
            geom=geom
        )
        if created:
            self.createdCount += 1
        else:
            self.updateCount += 1
        return created


class MapsLayerCreateView(CampViewMixin, OrgaTeamPermissionMixin, CreateView):
    model = Layer
    template_name = "maps_layer_form.html"
    fields = [
        "name",
        "slug",
        "description",
        "icon",
        "group",
        "camp",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_success_url(self):
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class MapsLayerUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
    model = Layer
    slug_url_kwarg = "layer_slug"
    template_name = "maps_layer_form.html"
    fields = [
        "name",
        "slug",
        "description",
        "icon",
        "group",
        "camp",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_success_url(self):
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class MapsLayerDeleteView(CampViewMixin, OrgaTeamPermissionMixin, DeleteView):
    model = Layer
    template_name = "maps_layer_delete.html"
    slug_url_kwarg = "layer_slug"

    def delete(self, *args, **kwargs):
        for layer in self.get_object().features.all():
            layer.delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "The Layer has been deleted")
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class MapsFeaturesView(LayerViewMixin, OrgaTeamPermissionMixin, ListView):
    model = Feature
    template_name = "maps_layer_feature_list_backoffice.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = Feature.objects.filter(layer=self.layer)
        return context


class MapsFeatureCreateView(LayerViewMixin, OrgaTeamPermissionMixin, CreateView):
    model = Feature
    template_name = "maps_feature_form.html"
    fields = [
        "name",
        "description",
        "url",
        "topic",
        "processing",
        "icon",
        "color",
        "layer",
        "geom",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        form.fields['layer'].initial = self.layer.pk
        form.fields['layer'].disabled = True
        form.fields["geom"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                'map_height': '500px',
                'geom_type': 'GeometryCollection',
            },
        )
        return form

    def get_success_url(self):
        messages.success(self.request, "The feature has been created")
        return reverse(
            "backoffice:maps_features_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"], "layer_slug": self.layer.slug},
        )


class MapsFeatureUpdateView(LayerViewMixin, OrgaTeamPermissionMixin, UpdateView):
    model = Feature
    slug_url_kwarg = "feature_uuid"
    slug_field = "uuid"
    template_name = "maps_feature_form.html"
    fields = [
        "name",
        "description",
        "url",
        "topic",
        "processing",
        "icon",
        "color",
        "geom",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        form.fields["geom"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                'map_height': '500px',
                'geom_type': 'GeometryCollection',
            },
        )
        return form

    def get_success_url(self):
        messages.success(self.request, "The feature has been updated")
        return reverse(
            "backoffice:maps_features_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"], "layer_slug": self.layer.slug},
        )


class MapsFeatureDeleteView(LayerViewMixin, OrgaTeamPermissionMixin, DeleteView):
    model = Feature
    template_name = "maps_feature_delete.html"
    slug_url_kwarg = "feature_uuid"
    slug_field = "uuid"

    def get_success_url(self):
        messages.success(self.request, "The feature has been deleted")
        return reverse(
            "backoffice:maps_features_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"], "layer_slug": self.layer.slug},
        )


class MapsExternalLayerCreateView(OrgaTeamPermissionMixin, CreateView):
    model = ExternalLayer
    template_name = "maps_external_layer_form.html"
    fields = [
        "name",
        "description",
        "camp",
        "url",
    ]

    def get_success_url(self):
        messages.success(self.request, "The external layer has been created")
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapsExternalLayerUpdateView(OrgaTeamPermissionMixin, UpdateView):
    model = ExternalLayer
    slug_url_kwarg = "external_layer_uuid"
    slug_field = "uuid"
    template_name = "maps_external_layer_form.html"
    fields = [
        "name",
        "description",
        "camp",
        "url",
    ]

    def get_success_url(self):
        messages.success(self.request, "The external layer has been updated")
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapsExternalLayerDeleteView(OrgaTeamPermissionMixin, DeleteView):
    model = ExternalLayer
    template_name = "maps_external_layer_delete.html"
    slug_url_kwarg = "external_layer_uuid"
    slug_field = "uuid"
    context_object_name = "external_layer"

    def get_success_url(self):
        messages.success(self.request, "The external layer has been deleted")
        return reverse(
            "backoffice:maps_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )
