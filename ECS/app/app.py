from flask import Flask, redirect, render_template, request, url_for
import os
from datetime import datetime, timezone

app = Flask(__name__)
items = []
APP_VERSION = os.getenv("APP_VERSION", "v1")


@app.get("/")
def index():
    return render_template("index.html", items=items, version=APP_VERSION)


@app.post("/items")
def add_item():
    title = request.form.get("title", "").strip()
    if title:
        items.append({
            "id": len(items) + 1,
            "title": title[:120],
            "done": False,
            "created_at": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        })
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/toggle")
def toggle_item(item_id):
    for item in items:
        if item["id"] == item_id:
            item["done"] = not item["done"]
            break
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/delete")
def delete_item(item_id):
    items[:] = [item for item in items if item["id"] != item_id]
    return redirect(url_for("index"))


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
