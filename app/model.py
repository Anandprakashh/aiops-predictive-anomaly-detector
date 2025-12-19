import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from sklearn.ensemble import IsolationForest


def get_es_client():
    es_host = os.getenv("ES_HOST", "http://localhost:9200")
    es_user = os.getenv("ES_USERNAME", "")
    es_pass = os.getenv("ES_PASSWORD", "")

    # For local dev: allow self-signed certs
    verify_certs = os.getenv("ES_VERIFY_CERTS", "false").lower() == "true"

    if es_user and es_pass:
        return Elasticsearch(
            es_host,
            #basic_auth=(es_user, es_pass),
            http_auth=(es_user, es_pass),
            verify_certs=verify_certs,
            ssl_show_warn=not verify_certs,
        )
    return Elasticsearch(
        es_host,
        verify_certs=verify_certs,
        ssl_show_warn=not verify_certs,
    )

    #if es_user and es_pass:
     #   return Elasticsearch(es_host, basic_auth=(es_user, es_pass))
    #return Elasticsearch(es_host)


def fetch_recent_logs(index_pattern="*", minutes=15, size=500):
    """
    Fetch recent logs from Elasticsearch.
    """
    es = get_es_client()
    now = datetime.utcnow()
    start = now - timedelta(minutes=minutes)

    body = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start.isoformat(),
                    "lte": now.isoformat()
                }
            }
        },
        "_source": ["@timestamp", "log", "message", "level", "kubernetes.pod_name"],
        "size": size,
        "sort": [{"@timestamp": {"order": "desc"}}],
    }

    res = es.search(index=index_pattern, body=body)
    docs = []
    for hit in res["hits"]["hits"]:
        src = hit["_source"]
        msg = src.get("message") or src.get("log") or ""
        lvl = (src.get("level") or "").upper()
        pod = src.get("kubernetes", {}).get("pod_name", "unknown")

        docs.append(
            {
                "timestamp": src.get("@timestamp"),
                "message": msg,
                "level": lvl,
                "pod": pod,
            }
        )
    return pd.DataFrame(docs)
    
    #Feature engineering + Isolation Forest
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["is_error", "msg_len", "has_exception", "has_timeout"])

    messages = df["message"].fillna("").str.lower()

    return pd.DataFrame(
        {
            "is_error": df["level"].fillna("").str.contains("ERROR", case=False).astype(int),
            "msg_len": messages.str.len(),
            "has_exception": messages.str.contains("exception").astype(int),
            "has_timeout": messages.str.contains("timeout|timed out").astype(int),
        }
    )


def score_anomalies(df: pd.DataFrame, contamination: float = 0.1):
    """
    Train a simple IsolationForest on recent logs and return anomaly scores.
    """
    features = build_features(df)
    if features.empty:
        return None, None

    model = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state=42,
    )
    model.fit(features)

    # anomaly scores: lower = more abnormal
    scores = model.decision_function(features)
    labels = model.predict(features)  # -1 = anomaly, 1 = normal

    df_out = df.copy()
    df_out["anomaly_score"] = scores
    df_out["anomaly_label"] = labels
    return df_out, model


def detect_recent_anomalies(index_pattern="*", minutes=15, contamination=0.1, threshold_label=-1):
    df = fetch_recent_logs(index_pattern=index_pattern, minutes=minutes)
    if df.empty:
        return {"count": 0, "anomalies": []}

    scored, _ = score_anomalies(df, contamination=contamination)
    if scored is None:
        return {"count": 0, "anomalies": []}

    anomalies = scored[scored["anomaly_label"] == threshold_label]
    top = (
        anomalies.sort_values("anomaly_score")
        .head(10)[["timestamp", "pod", "level", "message", "anomaly_score"]]
        .to_dict(orient="records")
    )

    return {
        "count": int(len(anomalies)),
        "window_minutes": minutes,
        "examples": top,
    }
