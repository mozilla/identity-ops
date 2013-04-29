#!/bin/bash

# metrics_server:/opt/bid_metrics/queue/*.webheadname
# zcat metrics_server:/opt/bid_metrics/queue/*.verifier-metrics.webheadname > /opt/bid_metrics/etl/input/verifier-metrics.json
# zcat metrics_server:/opt/bid_metrics/queue/*.router-metrics.webheadname > /opt/bid_metrics/etl/input/router-metrics.json
# metrics_server: run.sh
# metrics-logger1.private.scl3.mozilla.com:/home/bid_metrics/

server="10.22.75.50" # metrics-logger1.private.scl3.mozilla.com

RESULT=$( {
    set -x
    set -v
    if [[ "$USER" != "bid_metrics" ]]; then
        echo "This script must be run as the user 'bid_metrics'!"
        exit 1
    fi
    mv /opt/bid_metrics/incoming/* /opt/bid_metrics/queue/
    > /opt/bid_metrics/etl/input/router-metrics.json > /opt/bid_metrics/etl/input/verifier-metrics.json
    for file in /opt/bid_metrics/queue/*; do
        if expr "$file" : ".*verifier-metrics.*" >/dev/null; then
            target="/opt/bid_metrics/etl/input/verifier-metrics.json"
        elif expr "$file" : ".*router-metrics." >/dev/null; then
            target="/opt/bid_metrics/etl/input/router-metrics.json"
        elif expr "$file" : ".*browserid-metrics." >/dev/null; then
            continue
        else
            echo "unknown input file $file" >&2
            exit 1
        fi
        zcat $file >> $target
    done
    cd /opt/bid_metrics/etl
    if ! ./run.sh; then
        echo "** etl run.sh failed" >&2
        exit 2
    fi
    
    # we need to keep a logfile or two worth of data for context
    find /opt/bid_metrics/queue -type f -mtime +30 -delete

    if ! scp -q /opt/bid_metrics/etl/output/* $server:/home/bid_metrics/incoming/ && mv /opt/bid_metrics/etl/output/* /opt/bid_metrics/etl/pushed/; then
        echo "failed to push scrubbed metrics to $server"
        exit 3
    fi
    exit 0
} 2>&1 ); rc=$?;

if [[ "$VERBOSE" -gt 0 ]]; then
    echo "Verbose output:\n\n$RESULT"
fi
if [[ "$rc" -ne 0 ]]; then
    /usr/sbin/sendmail -t <<EOF
From: "$HOSTNAME bid metrics processor" <bid-metrics-processor@$HOSTNAME>
To: gene@mozilla.com, njslrc25jfqd@nmamail.net, cron-weave@mozilla.com, metrics-alerts@mozilla.org
Subject: $HOSTNAME failed to process metrics

$HOSTNAME failed to process metrics

$RESULT
EOF
    exit 2
fi
