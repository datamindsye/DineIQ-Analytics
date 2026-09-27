"""SparkSession factory and local configuration management."""

import os
import sys

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
        # Guarantee that Spark Python workers execute using the active Python interpreter
        os.environ["PYSPARK_PYTHON"] = sys.executable
        os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

        # Configure JAVA_HOME if not set in environment
        if "JAVA_HOME" not in os.environ:
            for candidate in [
                r"C:\Program Files\Java\jdk-17",
                r"C:\Program Files\Java\jdk-21",
                r"C:\Program Files\Eclipse Adoptium\jdk-17",
            ]:
                if os.path.exists(candidate):
                    os.environ["JAVA_HOME"] = candidate
                    java_bin = os.path.join(candidate, "bin")
                    if java_bin not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = java_bin + ";" + os.environ.get("PATH", "")
                    break

        # Configure HADOOP_HOME and PATH for Windows native filesystem committers
        if os.path.exists(r"C:\hadoop"):
            os.environ["HADOOP_HOME"] = r"C:\hadoop"
            os.environ["hadoop.home.dir"] = r"C:\hadoop"
            bin_dir = r"C:\hadoop\bin"
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + ";" + os.environ.get("PATH", "")

        from pyspark.sql import SparkSession

        builder = (
            SparkSession.builder.appName(app_name)
            .master("local[*]")
            .config("spark.pyspark.python", sys.executable)
            .config("spark.pyspark.driver.python", sys.executable)
            .config("spark.driver.memory", "2g")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        )
        if os.path.exists(r"C:\hadoop"):
            builder = builder.config("spark.hadoop.hadoop.home.dir", r"C:\hadoop")

        spark = builder.getOrCreate()
        return spark
    except Exception as exc:
        logger.error("Failed to initialize SparkSession: %s", exc)
        return None
