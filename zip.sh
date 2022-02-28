#!/bin/bash

mkdir zipped
cd zipped
cp ../src/* .
mkdir shipper
cp ../shipper/shipper.py shipper
zip lambda_function lambda_function.py shipper/*
cd ..
mv zipped/lambda_function.zip .
rm -rf zipped