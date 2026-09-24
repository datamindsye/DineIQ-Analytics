"""SparkSession factory and local configuration management."""

from packages.common.logging import get_logger

logger = get_logger(__name__)


def is_spark_available() -> bool:
    """Check if PySpark is installed and importable."""
    try:
        import pyspark  # noqa: F401

        return True
    except ImportError:
        return False


def get_spark_session(app_name: str = "DineIQ-Spark-Analytics") -> object | None:
    """Create or retrieve a local SparkSession with optimized development settings.

    Returns None if PySpark is not installed, logging a warning rather than raising.
    """
    if not is_spark_available():
        logger.warning("PySpark is not installed or available in this environment.")
        return None

    try:
        from pyspark.sql import SparkSession

        spark = (
            SparkSession.builder.appName(app_name)
            .master("local[*]")
            .config("spark.driver.memory", "2g")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .getOrCreate()
        )
        return spark
    except Exception as exc:
        logger.error("Failed to initialize SparkSession: %s", exc)
        return None
