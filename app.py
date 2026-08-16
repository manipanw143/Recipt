from flask import Flask
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from models import db
from schemas import blp

app = Flask(__name__)

# PostgreSQL config
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://manish:welcome@localhost/school_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["API_TITLE"] = "School API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

db.init_app(app)
ma = Marshmallow(app)
api = Api(app)

# Register blueprint
api.register_blueprint(blp)

if __name__ == "__main__":
    app.run(debug=True)
