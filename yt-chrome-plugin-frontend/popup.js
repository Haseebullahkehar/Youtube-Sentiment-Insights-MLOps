document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("analyzeBtn");
  const output = document.getElementById("output");

  btn.addEventListener("click", async () => {
    const videoId = document.getElementById("videoId").value.trim();
    if (!videoId) {
      alert("Please enter a YouTube video ID");
      return;
    }

    output.innerHTML = "<p>Fetching comments...</p>";

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId }),
      });

      const data = await res.json();
      if (data.error) {
        output.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
        return;
      }

      // Show metrics
      output.innerHTML = `
        <div class="metrics-container">
          <div class="metric"><div class="metric-title">Positive</div><div class="metric-value">${data.positive}</div></div>
          <div class="metric"><div class="metric-title">Neutral</div><div class="metric-value">${data.neutral}</div></div>
          <div class="metric"><div class="metric-title">Negative</div><div class="metric-value">${data.negative}</div></div>
          <div class="metric"><div class="metric-title">Total</div><div class="metric-value">${data.total_comments}</div></div>
        </div>

        <div class="section-title">Word Cloud</div>
        <img src="${data.wordcloud}" alt="Word Cloud" />

        <div class="section-title">Sentiment Chart</div>
        <img src="${data.sentiment_chart}" alt="Sentiment Chart" />

        <div class="section-title">Sample Comments</div>
        <ul class="comment-list">
          ${data.comments
            .map(
              (c) =>
                `<li class="comment-item"><span>${c.comment}</span><br><span class="comment-sentiment">Sentiment: ${c.sentiment}</span></li>`
            )
            .join("")}
        </ul>
      `;
    } catch (err) {
      console.error("Error:", err);
      output.innerHTML = `<p style="color:red;">Failed to fetch analysis</p>`;
    }
  });
});
