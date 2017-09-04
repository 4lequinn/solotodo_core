import traceback

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geoip2 import GeoIP2
from django.db import models, IntegrityError
from django.http import Http404
from django.utils import timezone
from django_filters import rest_framework
from geoip2.errors import AddressNotFoundError
from guardian.shortcuts import get_objects_for_user
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import list_route, detail_route
from rest_framework import exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, \
    SearchFilter
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.reverse import reverse

from solotodo.decorators import detail_permission
from solotodo.drf_extensions import PermissionReadOnlyModelViewSet
from solotodo.filters import EntityFilterSet, StoreUpdateLogFilterSet, \
    ProductFilterSet, EntityHistoryFilterSet
from solotodo.forms.entity_state_form import EntityStateForm
from solotodo.forms.ip_form import IpForm
from solotodo.forms.category_form import CategoryForm
from solotodo.models import Store, Language, Currency, Country, StoreType, \
    Category, StoreUpdateLog, Entity, Product, NumberFormat, EntityHistory, \
    EntityState
from solotodo.pagination import StoreUpdateLogPagination, EntityPagination, \
    ProductPagination, EntityPriceHistoryPagination
from solotodo.serializers import UserSerializer, LanguageSerializer, \
    StoreSerializer, CurrencySerializer, CountrySerializer, \
    StoreTypeSerializer, StoreUpdatePricesSerializer, CategorySerializer, \
    StoreUpdateLogSerializer, EntitySerializer, ProductSerializer, \
    NumberFormatSerializer, EntityEventUserSerializer, \
    EntityEventValueSerializer, EntityHistorySerializer, EntityStateSerializer
from solotodo.tasks import store_update
from solotodo.utils import get_client_ip


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    @list_route(methods=['get', 'patch'],
                permission_classes=(permissions.IsAuthenticated, ))
    def me(self, request):
        user = request.user

        if request.method == 'PATCH':
            content = JSONParser().parse(request)
            serializer = UserSerializer(
                user, data=content, partial=True,
                context={'request': request})
            if serializer.is_valid(raise_exception=True):
                serializer.save()

        payload = UserSerializer(
            user,
            context={'request': request}).data

        payload['url'] = reverse('solotodouser-me', request=request)
        return Response(payload)


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class NumberFormatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NumberFormat.objects.all()
    serializer_class = NumberFormatSerializer


class StoreTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StoreType.objects.all()
    serializer_class = StoreTypeSerializer


class EntityStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EntityState.objects.all()
    serializer_class = EntityStateSerializer


class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class CategoryViewSet(PermissionReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    @list_route()
    def by_ip(self, request):
        if 'ip' in request.query_params:
            form = IpForm(request.query_params)
        else:
            form = IpForm({'ip': get_client_ip(request)})

        if form.is_valid():
            geo_ip2 = GeoIP2()
            try:
                country_data = geo_ip2.country(form.cleaned_data['ip'])
            except AddressNotFoundError as err:
                raise exceptions.NotFound(err)
            try:
                country = Country.objects.get(
                    iso_code=country_data['country_code'])
            except Country.DoesNotExist as err:
                raise exceptions.NotFound(err)
        else:
            raise exceptions.ValidationError({'detail': 'Invalid IP address'})

        serializer = CountrySerializer(
            country,
            context={'request': request})
        return Response(serializer.data)


class StoreViewSet(PermissionReadOnlyModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_queryset(self):
        return get_objects_for_user(self.request.user, 'view_store',
                                    klass=Store)

    @detail_route()
    @detail_permission('update_store_pricing')
    def scraper(self, request, pk):
        store = self.get_object()
        try:
            store.scraper
        except AttributeError:
            raise Http404
        serializer = StoreUpdatePricesSerializer(
            store, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['post'])
    @detail_permission('update_store_pricing')
    def update_pricing(self, request, pk):
        store = self.get_object()
        serializer = StoreUpdatePricesSerializer(
            store, data=request.data, context={'request': request})

        if serializer.is_valid():
            validated_data = serializer.validated_data

            categories = validated_data['categories']
            if categories:
                category_ids = [pt.id for pt in categories]
            else:
                category_ids = None

            discover_urls_concurrency = \
                validated_data.get('discover_urls_concurrency')
            products_for_url_concurrency = \
                validated_data.get('products_for_url_concurrency')
            use_async = validated_data.get('async')

            store_update_log = StoreUpdateLog.objects.create(store=store)

            task = store_update.delay(
                store.id,
                category_ids=category_ids,
                extra_args=None,
                discover_urls_concurrency=discover_urls_concurrency,
                products_for_url_concurrency=products_for_url_concurrency,
                use_async=use_async,
                update_log_id=store_update_log.id
            )

            return Response({
                'task_id': task.id,
                'log_id': store_update_log.id
            })
        else:
            return Response(serializer.errors)


class StoreUpdateLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StoreUpdateLog.objects.all()
    serializer_class = StoreUpdateLogSerializer
    pagination_class = StoreUpdateLogPagination
    filter_backends = (rest_framework.DjangoFilterBackend, OrderingFilter)
    filter_class = StoreUpdateLogFilterSet
    ordering_fields = ('last_updated', )

    @list_route()
    def latest(self, request, *args, **kwargs):
        stores = get_objects_for_user(
            self.request.user, 'view_store_update_logs', klass=Store)

        result = {}

        for store in stores:
            store_url = reverse('store-detail', kwargs={'pk': store.pk},
                                request=request)
            store_latest_log = store.storeupdatelog_set.order_by(
                '-last_updated')[:1]

            if store_latest_log:
                store_latest_log = StoreUpdateLogSerializer(
                    store_latest_log[0], context={'request': request}).data
            else:
                store_latest_log = None

            result[store_url] = store_latest_log

        return Response(result)


class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    pagination_class = EntityPagination
    filter_backends = (rest_framework.DjangoFilterBackend, SearchFilter)
    filter_class = EntityFilterSet
    search_fields = ('product__instance_model__unicode_representation',
                     'cell_plan__instance_model__unicode_representation',
                     'name',
                     'cell_plan_name',
                     'part_number',
                     'sku',
                     'key',
                     'url',
                     'discovery_url')

    def dispatch_and_serialize_into_response(self, entity):
        def publish_callback(result, status):
            pass
            # handle publish result, status always present, result if
            # successful status.isError to see if error happened

        serialized_data = EntitySerializer(
            entity, context={'request': self.request}).data
        message = {
            'type': 'updateApiResourceObject',
            'resourceObject': serialized_data,
            'id': entity.id,
            'resource': 'entities',
            'user': reverse(
                'solotodouser-detail', kwargs={'pk': self.request.user.pk},
                request=self.request),
        }

        settings.PUBNUB.publish().channel(
            settings.BACKEND_CHANNEL).message(message).async(publish_callback)

        return Response(serialized_data)

    @detail_route(methods=['post'])
    def register_staff_access(self, request, *args, **kwargs):
        entity = self.get_object()
        if not entity.user_has_staff_perms(request.user):
            raise PermissionDenied

        entity.update_keeping_log(
            {
                'last_staff_access_user': request.user,
                'last_staff_access_date': timezone.now(),
            },
            request.user)
        return self.dispatch_and_serialize_into_response(entity)

    @detail_route(methods=['post'])
    def update_pricing(self, request, *args, **kwargs):
        entity = self.get_object()
        user = request.user

        has_perm = user.has_perm('update_store_pricing', entity.store) \
            or entity.user_has_staff_perms(user) \
            or user.has_perm('update_category_entities_pricing',
                             entity.category)

        if not has_perm:
            raise PermissionDenied

        try:
            entity.update_pricing(request.user)
            return self.dispatch_and_serialize_into_response(entity)
        except Exception as e:
            recipients = get_user_model().objects.filter(is_superuser=True)

            for recipient in recipients:
                recipient.send_entity_update_failure_email(
                    entity, request.user, traceback.format_exc())

            return Response({'detail': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @detail_route()
    def events(self, request, *args, **kwargs):
        entity = self.get_object()
        serialized_events = []

        def serialize_value(value):
            if isinstance(value, models.Model):
                return EntityEventValueSerializer(value).data
            else:
                return value

        for event in entity.events():
            serialized_changes = []
            for change in event['changes']:
                serialized_changes.append({
                    'field': change['field'],
                    'old_value': serialize_value(change['old_value']),
                    'new_value': serialize_value(change['new_value'])
                })

            serialized_event = {
                'timestamp': event['timestamp'],
                'user': EntityEventUserSerializer(
                    event['user'], context={'request': request}).data,
                'changes': serialized_changes
            }

            serialized_events.append(serialized_event)

        return Response(serialized_events)

    @detail_route(methods=['post'])
    def toggle_visibility(self, request, *args, **kwargs):
        entity = self.get_object()
        if not entity.user_has_staff_perms(request.user):
            raise PermissionDenied

        try:
            entity.update_keeping_log(
                {
                    'is_visible': not entity.is_visible,
                    'last_staff_change': timezone.now(),
                    'last_staff_change_user': request.user,
                },
                request.user)
            return self.dispatch_and_serialize_into_response(entity)
        except IntegrityError as err:
            return Response({'detail': str(err)},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def change_category(self, request, *args, **kwargs):
        entity = self.get_object()
        if not entity.user_has_staff_perms(request.user):
            raise PermissionDenied

        if entity.product:
            return Response({'detail': 'Cannot change category of '
                                       'associated entities'},
                            status=status.HTTP_400_BAD_REQUEST)

        form = CategoryForm(request.data)

        if form.is_valid():
            new_category = form.cleaned_data['category']
            if new_category == entity.category:
                return Response({'detail': 'The new category must be '
                                           'different from the original one'},
                                status=status.HTTP_400_BAD_REQUEST)

            entity.update_keeping_log(
                {
                    'category': new_category,
                    'last_staff_change': timezone.now(),
                    'last_staff_change_user': request.user,
                },
                request.user)
            return self.dispatch_and_serialize_into_response(entity)
        else:
            return Response({'detail': form.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def change_state(self, request, *args, **kwargs):
        entity = self.get_object()
        if not entity.user_has_staff_perms(request.user):
            raise PermissionDenied

        form = EntityStateForm(request.data)

        if form.is_valid():
            new_entity_state = form.cleaned_data['entity_state']
            if new_entity_state == entity.state:
                return Response({'detail': 'The new category must be '
                                           'different from the original one'},
                                status=status.HTTP_400_BAD_REQUEST)

            entity.update_keeping_log(
                {
                    'state': new_entity_state,
                    'last_staff_change': timezone.now(),
                    'last_staff_change_user': request.user,
                },
                request.user)
            return self.dispatch_and_serialize_into_response(entity)
        else:
            return Response({'detail': form.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['put', 'delete'])
    def association(self, request, *args, **kwargs):
        entity = self.get_object()
        if not entity.user_has_staff_perms(request.user):
            raise PermissionDenied

        if request.method == 'DELETE':
            if not entity.product:
                return Response(
                    {'detail': 'The entity is not associated'},
                    status=status.HTTP_400_BAD_REQUEST)

            entity.update_keeping_log({
                'product': None,
                'cell_plan': None,
                'last_association_user': None,
                'last_association_date': None,
            }, request.user)

            return self.dispatch_and_serialize_into_response(entity)

        if request.method == 'PUT':
            pass


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, SearchFilter)
    filter_class = ProductFilterSet
    pagination_class = ProductPagination


class EntityHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EntityHistory.objects.all()
    serializer_class = EntityHistorySerializer
    filter_backends = (rest_framework.DjangoFilterBackend, )
    filter_class = EntityHistoryFilterSet
    pagination_class = EntityPriceHistoryPagination
