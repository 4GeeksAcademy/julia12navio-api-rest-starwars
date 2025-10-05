"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Person, Planet, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


################################# MI CODIGO #############################

################################## USER
# GET USERS
@app.route('/user', methods=['GET'])
def handle_hello():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200

#GET FAVORITES USER
@app.route('/users/favorites', methods=['GET'])
def list_current_user_favorites():
    # Usuario fijo  (id = 1)
    user_id = 1

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"message": "User doesn't exist"}), 404

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200


# --- CREATE FAVORITES: PLANET ---
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id: int):
    user_id = 1  # "usuario actual" simulado

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"message": "User doesn't exist"}), 404

    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404

    # Evitar duplicados
    existing = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing:
        return jsonify({"message": "Planet already in favorites"}), 409

    fav = Favorite(user_id=user_id, planet_id=planet_id) 
    db.session.add(fav)
    db.session.commit()

    return jsonify(fav.serialize()), 201

# --- CREATE FAVORITES: PERSON ---
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id: int):
    user_id = 1  # "usuario actual" simulado

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"message": "User doesn't exist"}), 404

    person = db.session.get(Person, people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404

    # Evitar duplicados
    existing = Favorite.query.filter_by(user_id=user_id, person_id=people_id).first()
    if existing:
        return jsonify({"message": "Person already in favorites"}), 409

    fav = Favorite(user_id=user_id, person_id=people_id)  
    db.session.add(fav)
    db.session.commit()

    return jsonify(fav.serialize()), 201

# --- DELETE FAVORITE: PLANET ---
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def remove_favorite_planet(planet_id: int):
    user_id = 1  # "usuario actual" simulado

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"message": "User doesn't exist"}), 404

    fav = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if fav is None:
        return jsonify({"message": "Favorite planet not found"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Favorite planet removed"}), 200

# --- DELETE FAVORITE: PERSON ---
@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def remove_favorite_person(people_id: int):
    user_id = 1  # "usuario actual" simulado

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"message": "User doesn't exist"}), 404

    fav = Favorite.query.filter_by(user_id=user_id, person_id=people_id).first()
    if fav is None:
        return jsonify({"message": "Favorite person not found"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Favorite person removed"}), 200


############################################ PERSON

#GET PEOPLE
@app.route('/people', methods=['GET'])
def list_people():
    people = Person.query.all()
    return jsonify([p.serialize() for p in people]), 200

#GET PEOPLE BY ID
@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id: int):
    person = db.session.get(Person, people_id)

    if person is None:
        raise APIException("Person not found", status_code=404)

    return jsonify(person.serialize()), 200

# ---------- PEOPLE: CREATE ----------
@app.route('/people', methods=['POST'])
def create_person():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email') 
    gender = data.get('gender') 

    if not name:
        return jsonify({"message": "Field 'name' is required"}), 400

    person = Person(name=name, email=email, gender=gender)
    db.session.add(person)
    db.session.commit()
    return jsonify(person.serialize()), 201

# ---------- PEOPLE: UPDATE (PUT reemplaza) ----------
@app.route('/people/<int:people_id>', methods=['PUT'])
def update_person(people_id: int):
    data = request.get_json(silent=True) or {}

    person = db.session.get(Person, people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404

    name = data.get('name')
    if not name:
        return jsonify({"message": "Field 'name' is required"}), 400

    person.name = name
    person.email = data.get('email') 
    person.gender = data.get('gender') 

    db.session.commit()
    return jsonify(person.serialize()), 200

# ---------- PEOPLE: DELETE ----------
@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_person(people_id: int):
    person = db.session.get(Person, people_id)
    if person is None:
        return jsonify({"message": "Person not found"}), 404

    db.session.delete(person)
    db.session.commit()
    return jsonify({"message": "Person deleted"}), 200



################################################## PLANETS

# GET PLANETS
@app.route('/planets', methods=['GET'])
def list_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200

# GET PLANETS BY ID
@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id: int):
    planet = db.session.get(Planet, planet_id)  # SQLAlchemy 2.x
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    return jsonify(planet.serialize()), 200


# ---------- PLANETS: CREATE ----------
@app.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    climate = data.get('climate')
    terrain = data.get('terrain')
    population = data.get('population')

    if not name:
        return jsonify({"message": "Field 'name' is required"}), 400

    if population is not None:
        try:
            population = int(population)
        except (TypeError, ValueError):
            return jsonify({"message": "Field 'population' must be an integer"}), 400

    planet = Planet(name=name, climate=climate, terrain=terrain, population=population)
    db.session.add(planet)
    db.session.commit()
    return jsonify(planet.serialize()), 201


# ---------- PLANETS: UPDATE (PUT reemplaza) ----------
@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id: int):
    data = request.get_json(silent=True) or {}
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"message": "Field 'name' is required"}), 400

    climate = data.get('climate')
    terrain = data.get('terrain')
    population = data.get('population')

    if population is not None:
        try:
            population = int(population)
        except (TypeError, ValueError):
            return jsonify({"message": "Field 'population' must be an integer"}), 400

    planet.name = name
    planet.climate = climate
    planet.terrain = terrain
    planet.population = population
    db.session.commit()
    return jsonify(planet.serialize()), 200

# ---------- PLANETS: DELETE ----------
@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id: int):
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404

    # Evitar ForeignKeyViolation: borra favoritos que apunten a este planeta
    Favorite.query.filter_by(planet_id=planet_id).delete(synchronize_session=False)

    db.session.delete(planet)
    db.session.commit()
    return jsonify({"message": "Planet deleted"}), 200

##############################################################################

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
