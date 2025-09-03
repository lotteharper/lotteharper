#!/usr/bin/env python
from boto.s3.connection import S3Connection
import re
import datetime
import sys
import time

def main():
    s3_ID = sys.argv[1]
    s3_key = sys.argv[2]
    src_bucket_name = sys.argv[3]
    num_backup_buckets = sys.argv[4]
    connection = S3Connection(s3_ID, s3_key)
    copy_bucket("uglek", "lotteh")

def copy_bucket(src_bucket_name, dst_bucket_name, connection, maximum_keys = 100):
    src_bucket = connection.get_bucket(src_bucket_name);
    dst_bucket = connection.get_bucket(dst_bucket_name);

    result_marker = ''
    while True:
        keys = src_bucket.get_all_keys(max_keys = maximum_keys, marker = result_marker)

        for k in keys:
            print 'Copying ' + k.key + ' from ' + src_bucket_name + ' to ' + dst_bucket_name

            t0 = time.clock()
            dst_bucket.copy_key(k.key, src_bucket_name, k.key)
            print time.clock() - t0, ' seconds'

        if len(keys) < maximum_keys:
            print 'Done backing up.'
            break

        result_marker = keys[maximum_keys - 1].key

if  __name__ =='__main__': main()
