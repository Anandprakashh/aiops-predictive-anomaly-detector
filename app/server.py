from flask import Flask, jsonify
import os

from .model import detect_recent_anomalies

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "aiops-predictive-anomaly-detector"})

@app.route("/predict")
def predict():
    index_pattern = os.getenv("ES_INDEX_PATTERN", "*")
    minutes = int(os.getenv("ES_LOOKBACK_MINUTES", "15"))
    contamination = float(os.getenv("ANOMALY_CONTAMINATION", "0.1"))

    result = detect_recent_anomalies(
        index_pattern=index_pattern,
        minutes=minutes,
        contamination=contamination,
    )

    # simple “boolean” flag for GitOps automation
    anomaly_flag = result["count"] > 0
    return jsonify(
        {
            "anomaly": anomaly_flag,
            "details": result,
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
