import os
import boto3
from datetime import datetime, timedelta

REGION = os.getenv("AWS_REGION", "ap-south-1")

_cw_client = None

def get_cw_client():
    global _cw_client
    if _cw_client is None:
        try:
            _cw_client = boto3.client('cloudwatch', region_name=REGION)
        except Exception as e:
            print(f"Warning: Could not initialize CloudWatch client: {e}")
    return _cw_client

def get_alarm_state(alarm_name: str = "StockSentiment-HighDivergenceAlert") -> dict:
    """
    Returns current CloudWatch alarm status.
    """
    client = get_cw_client()
    if not client:
        return {"state": "UNKNOWN", "reason": "CloudWatch client offline"}

    try:
        resp = client.describe_alarms(AlarmNames=[alarm_name])
        alarms = resp.get('MetricAlarms', [])
        if alarms:
            alarm = alarms[0]
            return {
                "name": alarm['AlarmName'],
                "state": alarm['StateValue'],  # 'OK', 'ALARM', 'INSUFFICIENT_DATA'
                "reason": alarm.get('StateReason', ''),
                "updated": alarm.get('StateUpdatedTimestamp', '')
            }
        return {"state": "NOT_FOUND", "reason": "Alarm not configured"}
    except Exception as e:
        return {"state": "ERROR", "reason": str(e)}

def get_recent_metrics_summary():
    """
    Fetches recent metric telemetry from CloudWatch for the dashboard.
    """
    client = get_cw_client()
    if not client:
        return {}

    now = datetime.utcnow()
    start_time = now - timedelta(hours=6)

    try:
        metrics = client.list_metrics(Namespace='StockSentiment/Market')
        metric_list = []
        for m in metrics.get('Metrics', []):
            dimensions = {d['Name']: d['Value'] for d in m.get('Dimensions', [])}
            metric_list.append({
                'metric_name': m['MetricName'],
                'ticker': dimensions.get('Ticker', 'All')
            })
        return {
            'metric_count': len(metric_list),
            'metrics': metric_list
        }
    except Exception as e:
        print(f"Notice querying CloudWatch metrics: {e}")
        return {'metric_count': 0, 'metrics': []}

def publish_market_telemetry(max_divergence: float, flagged_count: int):
    """
    Publishes real-time divergence metrics directly to CloudWatch.
    """
    client = get_cw_client()
    if not client:
        return
    try:
        client.put_metric_data(
            Namespace='StockSentiment/Market',
            MetricData=[
                {
                    'MetricName': 'SentimentDivergenceSpread',
                    'Value': float(max_divergence),
                    'Unit': 'None'
                },
                {
                    'MetricName': 'HighDivergenceStockCount',
                    'Value': float(flagged_count),
                    'Unit': 'Count'
                }
            ]
        )
    except Exception as e:
        print(f"Notice publishing telemetry to CloudWatch: {e}")
