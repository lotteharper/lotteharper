#!/bin/bash
sudo sed -i -s $"8s@[0-9][0-9][0-9][0-9][0-9][0-9]@$1@g" /etc/banner
