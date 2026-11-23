from typing import Literal
from pydantic import BaseModel, Field

class DataPoint(BaseModel):
    timestamp: str
    value: float

class MetricSeries(BaseModel):
    metric_name: str
    unit: str
    resource_id: str
    resource_name: str
    data_points: list[DataPoint]

class MonitoringOverviewResponse(BaseModel):
    account_id: str
    region: str
    is_demo: bool
    time_range_hours: int
    has_metrics_permission: bool
    notice: str
    metrics: list[MetricSeries]
