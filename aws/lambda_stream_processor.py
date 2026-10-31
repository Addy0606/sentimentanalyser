import json
import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

deserializer = TypeDeserializer()
cloudwatch = boto3.client('cloudwatch', region_name='ap-south-1')

def deserialize_dynamodb_record(dynamo_dict):
    if not dynamo_dict:
        return {}
    return {k: deserializer.deserialize(v) for k, v in dynamo_dict.items()}

def lambda_handler(event, context):
    """
    Consumes DynamoDB Streams from StockSentiment-LiveFeed.
    Calculates retail vs institutional sentiment divergence, flags market anomalies,
    and publishes custom telemetry to Amazon CloudWatch.
    """
    records = event.get('Records', [])
    logger.info(f"Received {len(records)} stream record(s) from StockSentiment-LiveFeed.")

    ticker_stats = {}

    for record in records:
        event_name = record.get('eventName')  # INSERT, MODIFY, REMOVE
        if event_name != 'INSERT':
            continue

        dynamodb_data = record.get('dynamodb', {})
        new_image = deserialize_dynamodb_record(dynamodb_data.get('NewImage'))

        ticker = new_image.get('ticker', 'UNKNOWN')
        source = new_image.get('source', 'unknown')  # 'reddit' or 'news'
        sentiment = float(new_image.get('sentiment', 0.0))
        label = new_image.get('label', 'Neutral')
        title = new_image.get('title', '')
        timestamp = new_image.get('timestamp', '')

        if ticker not in ticker_stats:
            ticker_stats[ticker] = {
                'reddit_scores': [],
                'news_scores': [],
                'positive_count': 0,
                'negative_count': 0,
                'total': 0
            }

        stats = ticker_stats[ticker]
        stats['total'] += 1
        if label == 'Positive':
            stats['positive_count'] += 1
        elif label == 'Negative':
            stats['negative_count'] += 1

        if source.lower() == 'reddit':
            stats['reddit_scores'].append(sentiment)
        else:
            stats['news_scores'].append(sentiment)

        logger.info(
            f"[INGEST] Ticker: {ticker} | Source: {source.upper()} | Score: {sentiment:+.3f} ({label}) | "
            f"Title: {title[:70]}..."
        )

    # Calculate Divergence and Emit CloudWatch Metrics
    metric_data = []

    for ticker, stats in ticker_stats.items():
        avg_reddit = (sum(stats['reddit_scores']) / len(stats['reddit_scores'])) if stats['reddit_scores'] else None
        avg_news = (sum(stats['news_scores']) / len(stats['news_scores'])) if stats['news_scores'] else None

        divergence = 0.0
        divergence_alert = False

        if avg_reddit is not None and avg_news is not None:
            divergence = abs(avg_reddit - avg_news)
            if divergence >= 0.40:
                divergence_alert = True
                logger.warning(
                    f"⚠️ [DIVERGENCE ALERT] {ticker}: Retail (Reddit) Sentiment = {avg_reddit:+.2f} vs "
                    f"Institutional (News) Sentiment = {avg_news:+.2f} (Spread: {divergence:.2f})"
                )

        neg_ratio = (stats['negative_count'] / stats['total']) if stats['total'] > 0 else 0
        if neg_ratio >= 0.60:
            logger.warning(
                f"🚨 [SENTIMENT CRASH ALERT] {ticker}: {neg_ratio*100:.1f}% Negative sentiment across {stats['total']} items!"
            )

        # CloudWatch Custom Metrics
        metric_data.append({
            'MetricName': 'ProcessedSentimentItems',
            'Dimensions': [{'Name': 'Ticker', 'Value': ticker}],
            'Value': stats['total'],
            'Unit': 'Count'
        })

        if divergence > 0:
            metric_data.append({
                'MetricName': 'SentimentDivergenceSpread',
                'Dimensions': [{'Name': 'Ticker', 'Value': ticker}],
                'Value': divergence,
                'Unit': 'None'
            })

        if avg_reddit is not None:
            metric_data.append({
                'MetricName': 'RetailSentimentScore',
                'Dimensions': [{'Name': 'Ticker', 'Value': ticker}],
                'Value': avg_reddit,
                'Unit': 'None'
            })

    if metric_data:
        try:
            cloudwatch.put_metric_data(
                Namespace='StockSentiment/Market',
                MetricData=metric_data[:20]  # PutMetricData accepts up to 20 metrics per call
            )
            logger.info(f"Published {len(metric_data)} custom metric(s) to CloudWatch namespace 'StockSentiment/Market'.")
        except Exception as cw_err:
            logger.warning(f"CloudWatch metric publishing notice: {cw_err}")

    return {
        'statusCode': 200,
        'processed_tickers': list(ticker_stats.keys()),
        'records_count': len(records)
    }
