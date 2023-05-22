#!/usr/bin/env bash

public_ip_address=$(wget -qO- http://checkip.amazonaws.com)
echo "this computers public ip address is $public_ip_address"
aws ec2 revoke-security-group-ingress --region eu-central-1 --group-id sg-009639db96e5f36b5 --protocol tcp --port 22 --cidr "${public_ip_address}/32"
