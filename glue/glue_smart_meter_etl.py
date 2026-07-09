import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql import types as T


REQUIRED_ARGS = [
    "JOB_NAME",
    "RAW_S3_PATH",
    "PROCESSED_S3_PATH",
    "GLUE_DATABASE",
    "PROCESSED_TABLE_NAME",
]


def optional_arg(name, default):
    flag = f"--{name}"
    if flag in sys.argv:
        return getResolvedOptions(sys.argv, [name])[name]
    return default


args = getResolvedOptions(sys.argv, REQUIRED_ARGS)
clear_processed = optional_arg("CLEAR_PROCESSED", "false").lower() == "true"

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
spark.conf.set("spark.sql.parquet.compression.codec", "snappy")

raw_path = args["RAW_S3_PATH"]
processed_path = args["PROCESSED_S3_PATH"].rstrip("/") + "/"
database = args["GLUE_DATABASE"]
table_name = args["PROCESSED_TABLE_NAME"]

raw = (
    spark.read.option("header", "true")
    .option("inferSchema", "true")
    .option("mode", "PERMISSIVE")
    .csv(raw_path)
)

string_defaults = {
    "meter_id": "UNKNOWN",
    "battery_status": "Unknown",
    "firmware_version": "Unknown",
    "state": "Unknown",
    "district": "Unknown",
    "discom": "Unknown",
    "feeder_id": "Unknown",
    "health_status": "Unknown",
}

numeric_defaults = {
    "voltage": 0.0,
    "current": 0.0,
    "power_factor": 0.0,
    "battery_pct": 0,
    "rssi": 0.0,
    "consumption_kwh": 0.0,
}

boolean_defaults = {
    "voltage_issue": False,
    "power_factor_issue": False,
    "comm_issue": False,
    "signal_issue": False,
    "battery_issue": False,
}

df = raw
for column, default in {**string_defaults, **numeric_defaults, **boolean_defaults}.items():
    if column not in df.columns:
        df = df.withColumn(column, F.lit(default))

df = df.fillna(string_defaults).fillna(numeric_defaults).fillna(boolean_defaults)

df = (
    df.withColumn("meter_id", F.col("meter_id").cast(T.StringType()))
    .withColumn("timestamp", F.to_timestamp(F.col("timestamp")))
    .withColumn("voltage", F.col("voltage").cast(T.DoubleType()))
    .withColumn("current", F.col("current").cast(T.DoubleType()))
    .withColumn("power_factor", F.col("power_factor").cast(T.DoubleType()))
    .withColumn("last_communication_time", F.to_timestamp(F.col("last_communication_time")))
    .withColumn("battery_status", F.col("battery_status").cast(T.StringType()))
    .withColumn("battery_pct", F.col("battery_pct").cast(T.IntegerType()))
    .withColumn("rssi", F.col("rssi").cast(T.DoubleType()))
    .withColumn("firmware_version", F.col("firmware_version").cast(T.StringType()))
    .withColumn("state", F.col("state").cast(T.StringType()))
    .withColumn("district", F.col("district").cast(T.StringType()))
    .withColumn("discom", F.col("discom").cast(T.StringType()))
    .withColumn("feeder_id", F.col("feeder_id").cast(T.StringType()))
    .withColumn("consumption_kwh", F.col("consumption_kwh").cast(T.DoubleType()))
    .withColumn("voltage_issue", F.col("voltage_issue").cast(T.BooleanType()))
    .withColumn("power_factor_issue", F.col("power_factor_issue").cast(T.BooleanType()))
    .withColumn("comm_issue", F.col("comm_issue").cast(T.BooleanType()))
    .withColumn("signal_issue", F.col("signal_issue").cast(T.BooleanType()))
    .withColumn("battery_issue", F.col("battery_issue").cast(T.BooleanType()))
    .withColumn("health_status", F.col("health_status").cast(T.StringType()))
)

df = df.filter(F.col("meter_id").isNotNull() & F.col("timestamp").isNotNull())
df = df.dropDuplicates(["meter_id", "timestamp"])

issue_count = (
    F.col("voltage_issue").cast("int")
    + F.col("power_factor_issue").cast("int")
    + F.col("comm_issue").cast("int")
    + F.col("signal_issue").cast("int")
    + F.col("battery_issue").cast("int")
)

df = (
    df.withColumn("communication_lag_minutes", (F.col("timestamp").cast("long") - F.col("last_communication_time").cast("long")) / 60.0)
    .withColumn("issue_count", issue_count)
    .withColumn(
        "health_status",
        F.when(F.col("issue_count") >= 3, F.lit("Critical"))
        .when(F.col("issue_count") >= 1, F.lit("Warning"))
        .otherwise(F.lit("Healthy")),
    )
    .withColumn("event_date", F.to_date("timestamp"))
    .withColumn("year", F.year("timestamp"))
    .withColumn("month", F.lpad(F.month("timestamp").cast("string"), 2, "0"))
    .withColumn("day", F.lpad(F.dayofmonth("timestamp").cast("string"), 2, "0"))
)

ordered_columns = [
    "meter_id",
    "timestamp",
    "event_date",
    "voltage",
    "current",
    "power_factor",
    "last_communication_time",
    "communication_lag_minutes",
    "battery_status",
    "battery_pct",
    "rssi",
    "firmware_version",
    "state",
    "district",
    "discom",
    "feeder_id",
    "consumption_kwh",
    "voltage_issue",
    "power_factor_issue",
    "comm_issue",
    "signal_issue",
    "battery_issue",
    "issue_count",
    "health_status",
    "year",
    "month",
    "day",
]

df = df.select(*ordered_columns)

if clear_processed:
    glue_context.purge_s3_path(processed_path, options={"retentionPeriod": 0})

dynamic_frame = DynamicFrame.fromDF(df, glue_context, "smart_meter_processed")
sink = glue_context.getSink(
    path=processed_path,
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=["year", "month", "day"],
    enableUpdateCatalog=True,
    transformation_ctx="smart_meter_sink",
)
sink.setCatalogInfo(catalogDatabase=database, catalogTableName=table_name)
sink.setFormat("glueparquet", compression="snappy")
sink.writeFrame(dynamic_frame)

job.commit()
