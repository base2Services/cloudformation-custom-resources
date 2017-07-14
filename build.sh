#!/bin/bash

BUILD_NUMBER=$1
S3_BUCKET=$2
S3_REGION=$3

if [[ "x" == "x$BUILD_NUMBER" ]]; then
  BUILD_NUMBER="`cat package.json | jq '.version' -r`"
fi

if [[ "x" == "x$S3_REGION" ]]; then
  S3_REGION="ap-southeast-2"
fi

mkdir -p dist/
npm install

#sudo apt-get update -y && sudo apt-get install -y zip
zip -r dist/ccr-$BUILD_NUMBER.zip src/ node_modules/s

if [[ "x" != "x$S3_BUCKET" ]]; then
  aws s3 cp dist/ccr-$BUILD_NUMBER.zip s3://${S3_BUCKET}/build/ccr-$BUILD_NUMBER.zip --region $S3_REGION
fi
