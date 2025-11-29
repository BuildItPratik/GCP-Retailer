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

# BigQuery Configuration
BQ_PROJECT = "numeric-replica-471213-i0"
BQ_AUDIT_TABLE = f"{BQ_PROJECT}.temp_dataset.audit_log"
BQ_LOG_TABLE = f"{BQ_PROJECT}.temp_dataset.pipeline_logs"
BQ_TEMP_PATH = f"{GCS_BUCKET}/temp/"  

# MySQL Configuration
MYSQL_CONFIG = {
    "url": "jdbc:mysql://136.116.154.6:3306/retailerDB?useSSL=false&allowPublicKeyRetrieval=true",
    "driver": "com.mysql.cj.jdbc.Driver",
    "user": "myuser",
    "password": "Apple@1234"
}

# Initialize GCS & BigQuery Clients
storage_client = storage.Client()
bq_client = bigquery.Client()

# Logging Mechanism
log_entries = []  # Stores logs before writing to GCS
##---------------------------------------------------------------------------------------------------##

def log_event(event_type, message, table=None):
    """Log an event and store it in the log list"""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event_type": event_type,
        "message": message,
        "table": table
    }
    log_entries.append(log_entry)
    print(f"[{log_entry['timestamp']}] {event_type} - {message}")  # Print for visibility
    
##---------------------------------------------------------------------------------------------------##
    
# Function to Read Config File from GCS
def read_config_file():
    df = spark.read.csv(CONFIG_FILE_PATH, header=True)
    log_event("INFO", "✅ Successfully read the config file")
    return df

##---------------------------------------------------------------------------------------------------##

# Function to Move Existing Files to Archive
def move_existing_files_to_archive(table):
    blobs = list(storage_client.bucket(GCS_BUCKET).list_blobs(prefix=f"landing/retailer-db/{table}/"))
    existing_files = [blob.name for blob in blobs if blob.name.endswith(".json")]
    
    if not existing_files:
        log_event("INFO", f"No existing files for table {table}")
        return
    
    for file in existing_files:
        source_blob = storage_client.bucket(GCS_BUCKET).blob(file)
        
        # Extract Date from File Name (products_27032025.json)
        date_part = file.split("_")[-1].split(".")[0]
        year, month, day = date_part[-4:], date_part[2:4], date_part[:2]
        
        # Move to Archive
        archive_path = f"landing/retailer-db/archive/{table}/{year}/{month}/{day}/{file.split('/')[-1]}"
        destination_blob = storage_client.bucket(GCS_BUCKET).blob(archive_path)
        
        # Copy file to archive and delete original
        storage_client.bucket(GCS_BUCKET).copy_blob(source_blob, storage_client.bucket(GCS_BUCKET), destination_blob.name)
        source_blob.delete()
        
        log_event("INFO", f"✅ Moved {file} to {archive_path}", table=table)

    
##---------------------------------------------------------------------------------------------------##

# Main Execution
config_df = read_config_file()

for row in config_df.collect():
    if row["is_active"] == '1':
        db, src, table, load_type, watermark, _, targetpath = row
        move_existing_files_to_archive(table)
