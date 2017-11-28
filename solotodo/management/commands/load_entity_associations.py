import json
from datetime import datetime

import pytz
from django.core.management import BaseCommand
from django.utils import dateparse

from solotodo.models import Entity, Product, Category
from solotodo.utils import iterable_to_dict


class Command(BaseCommand):

    def handle(self, *args, **options):
        associations = json.load(open('entity_associations.json', 'r'))

        total_entity_count = len(associations)

        products_dict = iterable_to_dict(Product, 'id')
        categories_dict = iterable_to_dict(Category, 'id')

        entities_by_url = {}
        for entity in Entity.objects.all():
            if entity.url not in entities_by_url:
                entities_by_url[entity.url] = [entity]
            else:
                entities_by_url[entity.url].append(entity)

        for idx, url in enumerate(associations):
            print('{} / {}: {}'.format(idx + 1, total_entity_count, url))

            association_data = associations[url]

            if url not in entities_by_url:
                print('No entity found')
                continue

            entity = entities_by_url[url]
            if len(entity) > 1:
                print('More than one entity found for URL')
                continue
            entity = entity[0]

            if entity.product_id == association_data['product'] \
                    and entity.cell_plan_id == association_data[
                        'secondary_product'] \
                    and entity.last_association_user_id == \
                    association_data['user'] \
                    and entity.category_id == \
                    association_data['product_type'] \
                    and entity.is_visible == \
                    association_data['is_visible']:
                print('No changes found, skipping')
                continue

            if association_data['product'] and association_data['product'] \
                    not in products_dict:
                print('Product not found ' +
                      str(association_data['product']))
                continue

            if association_data['secondary_product'] and \
                    association_data['secondary_product'] not in products_dict:
                print('Product not found ' +
                      str(association_data['secondary_product']))
                continue

            entity.product_id = association_data['product']
            entity.cell_plan_id = association_data['secondary_product']
            entity.last_association_user_id = association_data['user']
            if association_data['date']:
                entity.last_association = pytz.utc.localize(
                    datetime.combine(
                        dateparse.parse_date(association_data['date']),
                        datetime.min.time()))
            else:
                entity.last_association = None
            entity.category = categories_dict[
                association_data['product_type']]
            entity.is_visible = association_data['is_visible']
            print('Saving entity')
            entity.save()
