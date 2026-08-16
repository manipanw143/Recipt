from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ✅ Use the correct table name
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://exampleapi:welcome@localhost:5432/myschool'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    __tablename__ = 'mystudents'  # Match your table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    age = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'age': self.age
        }

# ✅ Fix route to match React calls
@app.route('/mystudents', methods=['GET'])  # Remove trailing slash
def get_students():
    students = Student.query.all()
    return jsonify([s.to_dict() for s in students])

@app.route('/mystudents', methods=['POST'])  # Remove trailing slash
def add_student():
    data = request.get_json()
    try:
        student = Student(
            name=data['name'],
            email=data['email'],
            age=data['age']
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ✅ Add root route for testing
@app.route('/')
def home():
    return "Flask API is running!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)  # Explicit host/port