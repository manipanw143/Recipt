from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="School API", version="1.0.0")

class Student(BaseModel):
    id: int
    name: str
    email: str
    age: int

students_db: List[Student] = []

@app.post("/students", response_model=Student)
def create_student(student: Student):
    students_db.append(student)
    return student

@app.get("/students", response_model=List[Student])
def get_students():
    return students_db



