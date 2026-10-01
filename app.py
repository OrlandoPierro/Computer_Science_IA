from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.get("/")
    def home():
        return "ok"

    return app

if __name__ == "__main__":
    create_app().run(debug=True)