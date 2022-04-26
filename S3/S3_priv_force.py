import boto3
import os
import argparse
import botocore
from botocore.client import Config
import json
from colorama import Fore, Back, Style
from colorama import init
from tabulate import tabulate

init(autoreset=True)


parser = argparse.ArgumentParser()
parser.add_argument('--access-key', help='The aws_access_key_id you want to use.', default=None)
parser.add_argument('--secret-key', help='The aws_session_key you want to use.', default=None)
parser.add_argument('--session-token', help='The aws_session_token you want to use.', default=None)
parser.add_argument('--bucketname', help='Bucket name you want to enumerate.', default=None)
parser.add_argument('--bucketlist', help='File containing all the buckets you want to enumerate', default=None)
parser.add_argument('--region', help='Select the region you want to enumerate', default='us-east-2')
parser.add_argument('--raw-json', action='store_true', help='Flag to just print json repsonses from queries, default is False', default=False)
args = parser.parse_args()


def client_setup(access_key,secret_key,session_token,region):
    # Setup anonymous s3 client
    if access_key == None or secret_key == None:
        config = Config(connect_timeout=5,
                            read_timeout=5,
                            retries={'max_attempts': 5},
                            signature_version=botocore.UNSIGNED)
        try:
            client = boto3.client(
                's3',
                region_name=region,
                config=config
            )
            return client
        except Exception as e:
            print(e)
    else:
        # Setup authenticated s3 client
        config = Config(connect_timeout=5,
                            read_timeout=5,
                            retries={'max_attempts': 5})
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name=region,
                config=config
            )
            return client
        except Exception as e:
            print(e)




# Attempt to list
def list_buckets(client, region):
    print("listing buckets")
    try:
    # Retrieve the list of existing buckets
        response = client.list_buckets()
        # Output the bucket names
        for bucket in response['Buckets']:
            print(f'{bucket["Name"]}')
        # Enum all Buckets
        for bucket in response['Buckets']:
            enum_bucket(client, bucket["Name"])
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == "AccessDenied":
            print(f'{Fore.RED}Access to list buckets DENIED')
        else:
            print(f'{Fore.RED}Error code: {error.response["Error"]["Code"]}')
    except Except:
        print(e)


# read bucketnames from file then enum them
def bucketlist_enum(filename,client,region):
    with open(filename) as f:
        for line in f:
            print(line)
            enum_bucket(client, line.strip())


def enum_bucket(client, bucketname):
    print(f'================================')
    print(f'Enumerating bucket {bucketname}')

    # list bucket_list (ListBucket)
    try:
        response = client.list_objects_v2(Bucket=bucketname)
        print(f'{Fore.GREEN}Access to list bucket objects GRANTED listing files')
        file_list = []
        if args.raw_json:
            print(json.dumps(response, indent=4, default=str))
        else:
            for file in response["Contents"]:
                file_list.append([file["Key"], file["LastModified"]])
            print(f'{tabulate(file_list, headers=["File Name", "Last Modified"])}')

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == "AccessDenied":
            print(f'{Fore.RED}Access to list bucket objects DENIED')
        elif error.response['Error']['Code'] == "NoSuchBucket":
            print(f'{Fore.RED}Bucket not found')
    except Exception as e:
        print(e)

    # list object versions (ListBucketVersions)
    try:
        response = client.list_object_versions(Bucket=bucketname)
        print(f'{Fore.GREEN}Access to list bucket object versions GRANTED')
        file_version_list = []
        if args.raw_json:
            print(json.dumps(response, indent=4, default=str))
        else:
            for file in response["Versions"]:
                file_version_list.append([file["Key"], file["VersionId"], file["LastModified"]])
            print(tabulate(file_version_list, headers=["File Name", "Version ID", "Last Modified"]))

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == "AccessDenied":
            print(f'{Fore.RED}Access to list bucket object versions DENIED')
    except Exception as e:
        print(e)

    # get bucket notification configuration (GetBucketNotification)
    try:
        response = client.get_bucket_notification_configuration(Bucket=bucketname)
        print(f'{Fore.GREEN}Access to get bucket notificaitons configuration GRANTED')
        print(json.dumps(response, indent=4, default=str))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == "AccessDenied":
            print(f'{Fore.RED}Access to get bucket notifications DENIED')
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # if bucketname provided but nothing else can do anon scan
    if args.access_key is None and args.secret_key is None and args.bucketname is not None:
        print("Attempting anonymous bucket enumeration")
        client = client_setup(args.access_key,args.secret_key,args.session_token,args.region)
        enum_bucket(client,args.bucketname)

    elif ((args.access_key is None or args.secret_key is None) and args.bucketlist is None):
        print("Specify both access_key and secret_key or nethier to intiate anonymous scan")

    # do auth scan of specific bucket
    elif args.access_key is not None and args.secret_key is not None and args.bucketname is not None:
        print("Starting authenticated enumeration")
        client = client_setup(args.access_key,args.secret_key,args.session_token,args.region)
        enum_bucket(client,args.bucketname)
    # if no bucket name but auth
    elif args.access_key is not None and args.secret_key is not None and args.bucketname is None and args.bucketlist is None:
        client = client_setup(args.access_key,args.secret_key,args.session_token,args.region)
        list_buckets(client, args.region)

    # enum all buckets from a file
    elif args.bucketlist is not None:
        print("Starting bucket enum from file")
        client = client_setup(args.access_key,args.secret_key,args.session_token,args.region)
        bucketlist_enum(args.bucketlist,client,args.region)
