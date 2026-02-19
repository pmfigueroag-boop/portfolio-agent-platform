
import boto3
from services.shared.config import settings

try:
    s3 = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='admin', aws_secret_access_key='minioadmin', verify=False)
    bucket = 'portfolio-results'
    objs = s3.list_objects_v2(Bucket=bucket)
    if 'Contents' in objs:
        print(f"Deleting {len(objs['Contents'])} objects...")
        for o in objs['Contents']:
            s3.delete_object(Bucket=bucket, Key=o['Key'])
        print("Bucket cleared.")
    else:
        print("Bucket already empty.")
except Exception as e:
    print(f"Error: {e}")
