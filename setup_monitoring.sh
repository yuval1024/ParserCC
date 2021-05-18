#!/bin/bash

# prometheus node exporter:: https://prometheus.io/docs/guides/node-exporter/
wget https://github.com/prometheus/node_exporter/releases/download/v1.1.2/node_exporter-1.1.2.linux-amd64.tar.gz
tar xvfz node_exporter-1.1.2.linux-amd64.tar.gz
#cd node_exporter-1.1.2.linux-amd64/
/usr/bin/nohup ./node_exporter-1.1.2.linux-amd64/node_exporter &
