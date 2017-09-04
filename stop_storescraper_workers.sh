#!/usr/bin/env bash
celery multi stop -A solotodo_try storescraper_discover_urls_for_category storescraper_products_for_url storescraper_api --logfile=solotodo_try/logs/celery/%n.log --pidfile=solotodo_try/pids/celery/%n.pid -E -l info