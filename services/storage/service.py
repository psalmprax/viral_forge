import os
import logging
import boto3
from api.config import settings
from typing import Optional

class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.upper()
        self.bucket = settings.STORAGE_BUCKET
        self.s3_client = None
        
        # Determine credentials
        access_key = settings.STORAGE_ACCESS_KEY or settings.AWS_ACCESS_KEY_ID
        secret_key = settings.STORAGE_SECRET_KEY or settings.AWS_SECRET_ACCESS_KEY
        
        if self.provider == "LOCAL":
            logging.info("[StorageService] Initialized in LOCAL mode.")
            return

        try:
            from botocore import UNSIGNED
            from botocore.config import Config
            
            # Most providers (OCI, GCP, MinIO, NAS) are S3-compatible
            client_kwargs = {
                'service_name': 's3',
                'region_name': settings.STORAGE_REGION or settings.AWS_REGION
            }
            
            # Use credentials if provided, otherwise prepare for UNSIGNED access
            if access_key and secret_key:
                client_kwargs['aws_access_key_id'] = access_key
                client_kwargs['aws_secret_access_key'] = secret_key
            else:
                logging.warning(f"[StorageService] No access keys provided for {self.provider}. Attempting unsigned access.")
                client_kwargs['config'] = Config(signature_version=UNSIGNED)
            
            # Handle Custom Endpoints (OCI, NAS, GCP Interoperability)
            endpoint = settings.STORAGE_ENDPOINT
            
            if self.provider == "OCI":
                # Auto-fallback to standard OCI endpoint logic if not provided
                # Example: https://{namespace}.compat.objectstorage.{region}.oraclecloud.com
                if not endpoint:
                    logging.warning("[StorageService] OCI selected but STORAGE_ENDPOINT is missing.")
            
            if endpoint:
                client_kwargs['endpoint_url'] = endpoint
                logging.info(f"[StorageService] Using custom endpoint: {endpoint}")

            self.s3_client = boto3.client(**client_kwargs)
            logging.info(f"[StorageService] Initialized {self.provider} storage (Bucket: {self.bucket})")
            
        except Exception as e:
            logging.error(f"[StorageService] Failed to initialize {self.provider} storage: {e}")
            self.provider = "LOCAL"

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to the configured provider. 
        Returns the object key (Cloud) or absolute file path (Local).
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        if self.provider != "LOCAL" and self.s3_client:
            try:
                self.s3_client.upload_file(file_path, self.bucket, object_name)
                logging.info(f"[StorageService] Uploaded {file_path} to {self.provider}://{self.bucket}/{object_name}")
                return object_name
            except Exception as e:
                logging.error(f"[StorageService] {self.provider} upload failed: {e}")
                return file_path
        else:
            # Local storage fallback
            return os.path.abspath(file_path)

    def get_public_url(self, object_key_or_path: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL (Cloud) or returns a local static URL path.
        """
        if self.provider != "LOCAL" and self.s3_client and not object_key_or_path.startswith("/"):
            try:
                # OCI and standard S3 use the same presigned URL logic
                response = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': object_key_or_path},
                    ExpiresIn=expiration
                )
                return response
            except Exception as e:
                logging.error(f"[StorageService] Failed to generate presigned URL for {self.provider}: {e}")
                return object_key_or_path
        else:
            # Local fallback logic
            filename = os.path.basename(object_key_or_path)
            return f"{settings.PRODUCTION_DOMAIN}/static/outputs/{filename}"

base_storage_service = StorageService()
