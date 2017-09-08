from django.db.models import Q
from django_filters import rest_framework

from solotodo.filter_querysets import stores__view_store_update_logs, \
    stores__view_store_entities, categories__view_category_entities, \
    entities__view, categories__view_category_products, stores__view_store
from solotodo.models import Entity, StoreUpdateLog, Category, \
    Product, EntityHistory, Country


class StoreUpdateLogFilterSet(rest_framework.FilterSet):
    @property
    def qs(self):
        parent = super(StoreUpdateLogFilterSet, self).qs
        if self.request:
            stores_with_permission = stores__view_store_update_logs(
                self.request)
            return parent.filter(store__in=stores_with_permission)
        return parent

    class Meta:
        model = StoreUpdateLog
        fields = ('store',)


class EntityFilterSet(rest_framework.FilterSet):
    stores = rest_framework.ModelMultipleChoiceFilter(
        queryset=stores__view_store_entities,
        name='store',
        label='Stores'
    )
    categories = rest_framework.ModelMultipleChoiceFilter(
        queryset=categories__view_category_entities,
        name='category',
        label='Categories'
    )
    is_available = rest_framework.BooleanFilter(
        name='is_available', method='_is_available', label='Is available?')
    is_active = rest_framework.BooleanFilter(
        name='is_active', method='_is_active', label='Is active?')
    is_associated = rest_framework.BooleanFilter(
        name='is_associated', method='_is_associated', label='Is associated?')

    @property
    def qs(self):
        parent = super(EntityFilterSet, self).qs.select_related(
            'active_registry', 'product__instance_model')
        if self.request:
            categories_with_permission = categories__view_category_entities(
                self.request)
            stores_with_permission = stores__view_store_entities(self.request)

            return parent.filter(
                Q(category__in=categories_with_permission) &
                Q(store__in=stores_with_permission))
        return parent

    def _is_available(self, queryset, name, value):
        if value:
            return queryset.get_available()
        else:
            return queryset.get_unavailable()

    def _is_active(self, queryset, name, value):
        if value:
            return queryset.get_active()
        else:
            return queryset.get_inactive()

    def _is_associated(self, queryset, name, value):
        return queryset.filter(product__isnull=not value)

    class Meta:
        model = Entity
        fields = ['is_visible', ]


class ProductFilterSet(rest_framework.FilterSet):
    categories = rest_framework.ModelMultipleChoiceFilter(
        queryset=categories__view_category_products,
        name='instance_model__model__category',
        label='Categories'
    )
    availability_countries = rest_framework.ModelMultipleChoiceFilter(
        queryset=Country.objects.all(),
        label='Available in countries',
        method='_availability_countries'
    )
    availability_stores = rest_framework.ModelMultipleChoiceFilter(
        queryset=stores__view_store,
        label='Available in stores',
        method='_availability_stores'
    )
    last_updated = rest_framework.DateTimeFromToRangeFilter(
        name='last_updated'
    )
    creation_date = rest_framework.DateTimeFromToRangeFilter(
        name='creation_date'
    )
    keywords = rest_framework.CharFilter(
        label='Keywords',
        method='_keywords'
    )

    @property
    def qs(self):
        parent = super(ProductFilterSet, self).qs.select_related(
            'instance_model')
        if self.request:
            categories_with_permission = categories__view_category_products(
                self.request)

            parent = parent.filter_by_category(categories_with_permission)
        return parent.select_related('instance_model__model__category')

    def _availability_countries(self, queryset, name, value):
        if value:
            return queryset.filter_by_availability_in_countries(value)
        return queryset

    def _availability_stores(self, queryset, name, value):
        if value:
            return queryset.filter_by_availability_in_stores(value)
        return queryset

    def _keywords(self, queryset, name, value):
        if value:
            return queryset.filter_by_keywords(value)
        return queryset

    class Meta:
        model = Product
        fields = []


class EntityHistoryFilterSet(rest_framework.FilterSet):
    date = rest_framework.DateTimeFromToRangeFilter(
        name='timestamp'
    )
    available_only = rest_framework.BooleanFilter(
        method='_available_only',
        label='Available only?'
    )
    entities = rest_framework.ModelMultipleChoiceFilter(
        queryset=entities__view,
        name='entity',
        label='Entities'
    )

    @property
    def qs(self):
        parent = super(EntityHistoryFilterSet, self).qs.select_related()
        if self.request:
            categories_with_permission = categories__view_category_entities(
                self.request)
            stores_with_permission = stores__view_store_entities(self.request)

            return parent.filter(
                Q(entity__category__in=categories_with_permission) &
                Q(entity__store__in=stores_with_permission))
        return parent

    def _available_only(self, queryset, name, value):
        if value:
            return queryset.get_available()
        return queryset

    class Meta:
        model = EntityHistory
        fields = []
