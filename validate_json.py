
import boto3
import json
from services.shared.config import settings

try:
    s3 = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='admin', aws_secret_access_key='minioadmin', verify=False)
    objs = s3.list_objects_v2(Bucket='portfolio-results')
    
    if 'Contents' in objs:
        sorted_objs = sorted(objs['Contents'], key=lambda x: x['LastModified'], reverse=True)
        latest_key = sorted_objs[0]['Key']
        resp = s3.get_object(Bucket='portfolio-results', Key=latest_key)
        content = json.loads(resp['Body'].read().decode('utf-8'))
        
        print(f"--- Validating JSON Structure ({latest_key}) ---")
        print("Raw Content Keys:", list(content.keys()))
        print("Raw Content Sample:", json.dumps(content, indent=2)[:500])
        
        if 'run_id' not in content:
            print("FAILED: Missing 'run_id'")
        if 'results' not in content:
            print("FAILED: Missing 'results'")
        else:
             print(f"Result Count: {len(content['results'])}")
             if len(content['results']) > 0:
                 print("First item keys:", content['results'][0].keys())
    else:
        print('Bucket is empty.')
except Exception as e:
    print(f'Error: {e}')
