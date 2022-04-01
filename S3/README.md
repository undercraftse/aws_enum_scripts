# S3_priv_force
The script is a work in progress, intended to brute force permissions on an S3 bucket.

Currently works by passing AWS keys through command line arguments for authenticated scans.

Mostly based on CTFs
- Currently checks:
  - list buckets
  - list objects
  - list objects versions
  - Get bucket notification configuration (which may give additional information such as lambda function names, if there is any event triggers etc).

More checks will be added as they come up and prove useful.
