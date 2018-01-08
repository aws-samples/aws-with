## aws_with --output text -R '*' python show_spot_prices_globally.py

import datetime
import pytz
import boto3

now=datetime.datetime.now(pytz.UTC)
ec2=boto3.client("ec2")

prices=ec2.describe_spot_price_history(
    InstanceTypes=["m4.4xlarge"],
    ProductDescriptions=["Linux/UNIX"],
    StartTime=now)["SpotPriceHistory"]

for p in prices:
    print ("{},{}".format(p["AvailabilityZone"], p["SpotPrice"]))
