from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os
from dotenv import load_dotenv
#
# Load environment variables from .env file
load_dotenv(dotenv_path='pydev.env')

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/simple_route')
def simple_route():
    return jsonify(message='Welcome to Planetary APP!')


@app.route('/not_found')
def not_found():
    return jsonify(message='page not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message=f'{name} not old enough, Unauthorized'), 401
    else:
        return jsonify(message=f'{name}, Welcome to Planet APP!!')


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message=f'{name} not old enough, Unauthorized'), 401
    else:
        return jsonify(message=f'{name}, Welcome to Planet APP!!')


# cli command to create Database
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database Created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database Dropped')


# database seed
@app.cli.command('db_seed')
def db_seed():
    mercury = Planets(
        planet_name='Mercury',
        planet_type='Class D',
        home_star='Sol',
        mass=3.258e23,
        radius=1516,
        distance=35.98e6
    )
    venus = Planets(
        planet_name='Venus',
        planet_type='Class k',
        home_star='Sol',
        mass=4.86724,
        radius=3760,
        distance=67.24e6
    )
    earth = Planets(
        planet_name='Earth',
        planet_type='Class M',
        home_star='Sol',
        mass=5.972e24,
        radius=3959,
        distance=92.96e6
    )

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        name='William Hershel',
        email='william.hershel@bofa.com',
        password='P@ssw0rd'
    )

    db.session.add(test_user)
    db.session.commit()
    print('Database Seeded')


@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planets.query.all()
    result = planets_schema.dump(planet_list)
    return jsonify(result)
    # return jsonify(data=planet_list)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists.'), 409
    else:
        name = request.form['name']
        password = request.form['password']
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login Succeeded', access_token=access_token)
    else:
        return jsonify(message='Bad email/password'), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planets_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message=f"{planet_id} doesn't exist"),


@app.route('/add_planet')
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    planet = Planets.query.filter_by(planet_name=planet_name).first()
    if planet:
        return jsonify(message=f'{planet_name} already exist in the db'), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planets(planet_name=planet_name,
                             planet_type=planet_type,
                             home_star=home_star,
                             mass=mass,
                             radius=radius,
                             distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You added a planet"), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="You updated a planet"), 202
    else:
        return jsonify(message="That planet does not exist"), 404


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required
def remove_planet(planet_id: int):
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="You deleted a planet"), 202
    else:
        return jsonify(message="That planet does not exist"), 404


# database models
class User(db.Model):
    # table name
    __tablename__ = 'users'
    id = Column("id", Integer, primary_key=True)
    name = Column("name", String)
    email = Column("email", String, unique=True)
    password = Column("password", String)


class Planets(db.Model):
    ___tablename__ = 'planets'
    planet_id = Column("planet_id", Integer, primary_key=True)
    planet_name = Column("planet_name", String)
    planet_type = Column("planet_type", String)
    home_star = Column("home_star", String)
    mass = Column("mass", Float)
    radius = Column("radius", Float)
    distance = Column("distance", Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "password")


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ("planet_id", "planet_name", "planet_type", "home_star", "mass", "radius", "distance")


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
