
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Docker Flask Application</title>
    </head>
    <body>
        <h1>Welcome to My Dockerized Flask Application!</h1>
        <p>This application is running inside a Docker container.</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
