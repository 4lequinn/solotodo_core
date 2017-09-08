#!/usr/bin/env bash
celery multi start -A solotodo_try store_update general -Q:store_update store_update -c:store_update 5 -Q:general general -c:general 8 --logfile=solotodo_try/logs/celery/%n.log --pidfile=solotodo_try/pids/celery/%n.pid -E -l info