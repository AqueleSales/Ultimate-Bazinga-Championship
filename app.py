from bazinga import create_app
from bazinga.extensions import socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        debug=app.config["DEBUG"],
        host="127.0.0.1",
        port=int(__import__("os").getenv("PORT", "5000")),
    )
