#!/bin/bash

sudo docker build -t rca/frr frr/
sudo docker build -t rca/host host/
sudo docker build -t rca/server server/
