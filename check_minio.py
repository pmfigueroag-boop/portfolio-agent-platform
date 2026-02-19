import boto3
from services.shared.config import settings
try:
    s3 = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='admin', aws_secret_access_key='minioadmin', verify=False)
    objs = s3.list_objects_v2(Bucket='portfolio-results')
    if 'Contents' in objs:
        print(f"Found {len(objs['Contents'])} objects:")
        for o in objs['Contents'][-3:]:
             print(f"- {o['Key']} ({o['Size']} bytes)")
    else:
        print("Bucket is empty.")
except Exception as e:
    print(f"Error: {e}")
