#!/bin/bash

# read test pipeline configuration details...
source pipeline.cfg

# copy source files to a temporary directory...
ZIPDIR=`mktemp -d`
cp -R aws_with/ tests/ setup.py setup.cfg README.rst *.yml $ZIPDIR

# zip it up...
ZIP=`mktemp -u --suffix=.zip`
(
    cd $ZIPDIR
    zip -r $ZIP .
)

# copy the zip to S3...
aws s3 cp $ZIP $TEST_S3_PATH

# clean up...
rm $ZIP
rm -rf $ZIPDIR

# kick the pipeline...
aws codepipeline start-pipeline-execution --name $TEST_PIPELINE

