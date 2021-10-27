# AWS Public Certificate
Updated: 2020-08

The purpose of this folder is to contain the `AmazonRootCA1.pem` file so that we can version control
it. This file is set to expire at regular intervals so for future updates we need to ensure this
file is also included and that our daemon boot sequence includes code to check the hash difference
between the one saved in `$SNAP_COMMON` and `daemon/ident/aws`