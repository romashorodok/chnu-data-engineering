from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    avg,
    col,
    count,
    dense_rank,
    expr,
    max,
    month,
    to_date,
)

addr = "spark://spark-master:7077"

spark: SparkSession = SparkSession.builder.master(addr).getOrCreate()  # pyright: ignore

sc = spark.sparkContext
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", "minioadmin")  # pyright: ignore
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "minioadmin")  # pyright: ignore
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")  # pyright: ignore
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")  # pyright: ignore
sc._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")  # pyright: ignore
sc._jsc.hadoopConfiguration().set(  # pyright: ignore
    "fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
)
sc._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")  # pyright: ignore

df = spark.read.csv(
    "s3a://dataset/Divvy_Trips_2019_Q4.csv", header=True, inferSchema=True
)


def avg_trip_duration_per_day(df):
    df = df.withColumn("date", to_date("start_time", "yyyy-MM-dd"))

    result = (
        df.groupby("date")
        .agg(avg("tripduration").alias("avg_trip_duration"))
        .sort("date")
    )

    result.write.csv(
        "s3a://out/avg_trip_duration_per_day", header=True, mode="overwrite"
    )
    return result


def trip_count_per_day(df):
    df = df.withColumn("date", to_date("start_time", "yyyy-MM-dd"))
    result = df.groupby("date").agg(count("*").alias("trip_count_per_day")).sort("date")

    result.write.csv("s3a://out/trip_count_per_day", header=True, mode="overwrite")
    return result


def most_popular_start_station_per_month(df):
    df = df.withColumn("month", month("start_time"))

    trips_per_month_per_station = df.groupby("month", "from_station_name").agg(
        count("from_station_name").alias("trip_count")
    )

    window = Window.partitionBy("month").orderBy(col("trip_count").desc())

    result = (
        trips_per_month_per_station.withColumn("rank", dense_rank().over(window))
        .filter(col("rank") == 1)
        .drop("rank")
    )

    result.write.csv(
        "s3a://out/most_popular_start_station_per_month", header=True, mode="overwrite"
    )
    return result


def top3_stations_last_2_weeks(df):
    df = df.withColumn("date", to_date("start_time", "yyyy-MM-dd"))
    latest_date = df.select(max("date")).collect()[0][0]

    df_filtered = df.filter(col("date") >= latest_date - expr("INTERVAL 14 DAYS"))

    trip_count_df = df_filtered.groupBy("date", "to_station_name").agg(
        count("*").alias("trip_count")
    )

    window_spec = Window.partitionBy("date").orderBy(col("trip_count").desc())

    result = (
        trip_count_df.withColumn("rank", dense_rank().over(window_spec))
        .filter(col("rank") <= 3)
        .drop("rank")
        .sort(["date", "trip_count"])
    )

    result.write.csv(
        "s3a://out/top3_stations_last_2_weeks", header=True, mode="overwrite"
    )

    return result


def avg_trip_duration_by_gender(df):
    result = (
        df.filter(col("gender").isNotNull())
        .groupBy("gender")
        .agg(avg("tripduration").alias("avg_trip_duration"))
    )

    result.write.csv(
        "s3a://out/avg_trip_duration_by_gender", header=True, mode="overwrite"
    )
    return result


avg_trip_duration_per_day(df)
trip_count_per_day(df)
most_popular_start_station_per_month(df)
top3_stations_last_2_weeks(df)
avg_trip_duration_by_gender(df)
spark.stop()
