from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields

from models import db, Student

blp = Blueprint("Students", "students", url_prefix="/students", description="Operations on students")

class StudentSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    age = fields.Int()

@blp.route("/")
class StudentsList(MethodView):
    @blp.response(200, StudentSchema(many=True))
    def get(self):
        """List all students"""
        return Student.query.all()
