#!/bin/bash
set -Eeuxo pipefail

NGINX="nginx -c ${PWD}/nginx.conf -p ${PWD}"
PID="$(cat nginx.pid 2>/dev/null || true)"

case $1 in
    start)
        rm -rf *.log
        $NGINX
        trap "$0 stop; exit" SIGINT
        $0 log
        ;;
    stop)
        if [[ -n "${PID}" ]]; then
            $NGINX -s quit
        fi
        ;;
    restart)
        $0 stop
        $0 start
        ;;
    log)
        tail -f *.log
        ;;
    *)
        echo "$0 (start|stop|restart|log)"
        exit 1
esac
