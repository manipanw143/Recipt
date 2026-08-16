from flask import Flask
from flask_restx import Api, Resource, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://manish:welcome@localhost:5432/school_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app, 
          version='1.0', 
          title='School Database API',
          description='Swagger Documentation for school_db',
          doc='/swagger/')

def get_table_model(table_name):
    model_fields = {}
    query = text(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """)
    result = db.session.execute(query, {'table_name': table_name})
    for col in result:
        col_name = col[0]
        col_type = col[1]
        if col_type in ['integer', 'bigint', 'smallint', 'serial']:
            field = fields.Integer
        elif col_type in ['numeric', 'real', 'double precision']:
            field = fields.Float
        elif col_type == 'boolean':
            field = fields.Boolean
        elif col_type in ['character varying', 'text', 'varchar']:
            field = fields.String
        elif col_type == 'date':
            field = fields.Date
        elif col_type in ['timestamp', 'timestamp with time zone']:
            field = fields.DateTime
        else:
            field = fields.String
        model_fields[col_name] = field(description=col_type)
    return api.model(f'{table_name}_Model', model_fields)

@api.route('/tables')
class TableList(Resource):
    def get(self):
        inspector = inspect(db.engine)
        return {'tables': inspector.get_table_names()}

@api.route('/table/<string:table_name>')
class TableData(Resource):
    def get(self, table_name):
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if table_name not in tables:
            return {'error': f'Table "{table_name}" not found. Available tables: {tables}'}, 404

        # Dynamically create model for this table
        model = get_table_model(table_name)

        # Query data
        result = db.session.execute(text(f'SELECT * FROM "{table_name}" LIMIT 100'))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result]

        # Return marshaled data with dynamic model
        return data

    # Override method to attach dynamic model to swagger output
    @api.marshal_with(get_table_model.__func__, as_list=True)  # We'll fix this next
    def get(self, table_name):
        pass
