#!/bin/bash

# webhead:/opt/bid_metrics/queue/*
# metrics_server:/opt/bid_metrics/incoming/*.webheadname
# rm webhead:/opt/bid_metrics/queue/*

for file in /opt/bid_metrics/queue/*.json; do 
    mv $file /opt/bid_metrics/tmp/`basename $file`.$HOSTNAME
done

if ! scp -q /opt/bid_metrics/tmp/* $1:/opt/bid_metrics/incoming/; then
    /usr/sbin/sendmail -t <<EOF
From: "$HOSTNAME bid metrics pusher" <bid-metrics-pusher@$HOSTNAME>
To: gene@mozilla.com, njslrc25jfqd@nmamail.net
Subject: $HOSTNAME failed to push bid metrics to $server

$HOSTNAME failed to push bid metrics to $server
EOF
    exit 1
fi

rm -f /opt/bid_metrics/tmp/*
