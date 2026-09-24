"""Spark analytics and MLlib pipeline package."""

from packages.pipeline_spark.session import get_spark_session, is_spark_available

__all__ = ["get_spark_session", "is_spark_available"]
