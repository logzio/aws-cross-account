mkdir zipped
cd zipped
cp ../src/* .
mkdir shipper
cp ../shipper/shipper.py shipper
zip lambda_function lambda_function.py shipper/*