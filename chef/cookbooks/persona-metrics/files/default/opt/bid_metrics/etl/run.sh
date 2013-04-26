#!/bin/bash
export PENTAHO_DI_JAVA_OPTIONS='-Xmx8g -Xms6000m -Djava.io.tmpdir=/opt/bid_metrics/tmp'
cd kettle
./kitchen.sh -norep -file ../etl/main.kjb -param:DATE=$1
