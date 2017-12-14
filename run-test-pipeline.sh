#!/bin/bash

# read pipeline configuration options
source pipeline.cfg

# zip it up...
ZIP=`mktemp -u --suffix=.zip`
git ls-tree -r --name-only master | zip -@ $ZIP

# copy the zip to S3...
aws s3 cp $ZIP $TEST_S3_PATH

# clean up...
rm $ZIP
rm -rf $ZIPDIR

# kick the pipeline...
aws codepipeline start-pipeline-execution --name $TEST_PIPELINE

