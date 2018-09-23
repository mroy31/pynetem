#!/bin/sh

vtysh -c "show run" > $1
