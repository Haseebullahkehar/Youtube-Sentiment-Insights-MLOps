import os
import re
import pickle
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import numpy as np

# -------------------------
# App setup
# -------------------------
app = Flask(__name__)
CORS(app)

YOUTUBE_API_KEY = "AIzaSyCxD3Rh_jviq2an607H69RZtEQjrIgjUso"  # store key in environment variable

# -------------------------
# Load model & vectorizer
# -------------------------
with open("lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("tfidf_vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# -------------------------
# Preprocessing
# -------------------------
def preprocess_comment(comment):
    try:
        comment = comment.lower().strip()
        comment = re.sub(r"\n", " ", comment)
        comment = re.sub(r"[^A-Za-z0-9\s!?.,]", "", comment)

        stop_words = set(stopwords.words("english")) - {"not", "but", "no", "however", "yet"}
        comment = " ".join([w for w in comment.split() if w not in stop_words])

        lemmatizer = WordNetLemmatizer()
        comment = " ".join([lemmatizer.lemmatize(w) for w in comment.split()])
        return comment
    except Exception as e:
        print("Preprocessing error:", e)
        return comment

# -------------------------
# YouTube API Fetch
# -------------------------
def fetch_comments(video_id, max_results=50):
    url = (
        f"https://www.googleapis.com/youtube/v3/commentThreads"
        f"?part=snippet&videoId={video_id}&maxResults={max_results}&key={YOUTUBE_API_KEY}"
    )
    r = requests.get(url)
    data = r.json()

    comments = []
    if "items" in data:
        for item in data["items"]:
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
    return comments

# -------------------------
# Sentiment Prediction
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        video_id = request.json.get("video_id")
        if not video_id:
            return jsonify({"error": "No video_id provided"}), 400

        # fetch comments
        comments = fetch_comments(video_id)
        if not comments:
            return jsonify({"error": "No comments fetched"}), 404

        # preprocess
        processed = [preprocess_comment(c) for c in comments]
        X = vectorizer.transform(processed)
        preds = model.predict(X)

        # Map predictions: 0=neg, 1=neutral, 2=pos (adjust based on your model)
        sentiments = []
        for c, p in zip(comments, preds):
            if p == 0:
                label = "Negative"
            elif p == 1:
                label = "Neutral"
            else:
                label = "Positive"
            sentiments.append({"comment": c, "sentiment": label})

        # Metrics
        pos = np.sum(preds == 2)
        neu = np.sum(preds == 1)
        neg = np.sum(preds == 0)

        # Wordcloud
        all_text = " ".join(processed)
        wc = WordCloud(width=800, height=400, background_color="black").generate(all_text)
        buf = io.BytesIO()
        wc.to_image().save(buf, format="PNG")
        wc_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # Sentiment bar chart
        plt.figure(figsize=(4, 3))
        plt.bar(["Positive", "Neutral", "Negative"], [pos, neu, neg], color=["green", "gray", "red"])
        plt.title("Sentiment Distribution")
        buf2 = io.BytesIO()
        plt.savefig(buf2, format="PNG")
        buf2.seek(0)
        chart_b64 = base64.b64encode(buf2.getvalue()).decode("utf-8")
        plt.close()

        return jsonify({
            "video_id": video_id,
            "total_comments": len(comments),
            "positive": int(pos),
            "neutral": int(neu),
            "negative": int(neg),
            "comments": sentiments[:20],  # send top 20
            "wordcloud": f"data:image/png;base64,{wc_b64}",
            "sentiment_chart": f"data:image/png;base64,{chart_b64}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
