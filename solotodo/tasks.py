from celery import shared_task

from solotodo.models import Store, Category, StoreUpdateLog, Product


@shared_task(queue='store_update', ignore_result=True)
def store_update(store_id, category_ids=None,
                 discover_urls_concurrency=None,
                 products_for_url_concurrency=None,
                 use_async=None,
                 update_log_id=None):
    store = Store.objects.get(pk=store_id)

    if category_ids:
        categories = Category.objects.filter(pk__in=category_ids)
    else:
        categories = None

    categories = store.sanitize_categories_for_update(categories)

    sanitized_parameters = store.scraper.sanitize_parameters(
        discover_urls_concurrency=discover_urls_concurrency,
        products_for_url_concurrency=products_for_url_concurrency,
        use_async=use_async)

    discover_urls_concurrency = \
        sanitized_parameters['discover_urls_concurrency']
    products_for_url_concurrency = \
        sanitized_parameters['products_for_url_concurrency']
    use_async = sanitized_parameters['use_async']

    if update_log_id:
        update_log = StoreUpdateLog.objects.get(pk=update_log_id)
    else:
        update_log = StoreUpdateLog.objects.create(store=store)

    update_log.discovery_url_concurrency = discover_urls_concurrency
    update_log.products_for_url_concurrency = products_for_url_concurrency
    update_log.use_async = use_async
    update_log.save()

    update_log.categories = categories

    # Reset the categories to synchronize the task signature with the
    # actual method implementation
    if category_ids is None:
        categories = None

    store.update_pricing(
        categories=categories,
        discover_urls_concurrency=discover_urls_concurrency,
        products_for_url_concurrency=products_for_url_concurrency,
        use_async=use_async, update_log=update_log)


@shared_task(queue='store_update')
def store_update_pricing_from_json(store_id, json_data):
    store = Store.objects.get(pk=store_id)

    update_log = StoreUpdateLog.objects.create(
        store=store
    )

    update_log.categories = Category.objects.filter(
        storescraper_name__in=json_data['categories'])

    store.update_pricing_from_json(json_data, update_log=update_log)


@shared_task(queue='general', ignore_result=True)
def product_save(product_id):
    Product.objects.get(pk=product_id).save()
