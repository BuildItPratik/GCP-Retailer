from google.cloud import storage, bigquery
import pandas as pd
from pyspark.sql import SparkSession
import datetime
import json

# Initialize Spark Session
spark = SparkSession.builder.appName("RetailerMySQLToLanding").getOrCreate()

# Google Cloud Storage (GCS) Configuration variables
GCS_BUCKET = "retailer-bkt-27112025"
LANDING_PATH = f"gs://{GCS_BUCKET}/landing/retailer-db/"
ARCHIVE_PATH = f"gs://{GCS_BUCKET}/landing/retailer-db/archive/"
CONFIG_FILE_PATH = f"gs://{GCS_BUCKET}/configs/retailer_config.csv"