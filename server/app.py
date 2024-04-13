#!/usr/bin/env python3

from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)


@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    # adding the restaurants list to a dictionary
    restaurants_dict = [restaurant.to_dict(('id', 'name', 'address')) for restaurant in restaurants]
    return jsonify(restaurants_dict)

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    # adding the specific restaurant list to a dictionary
    serialized_restaurant = restaurant.to_dict(('id', 'name', 'address'))
    serialized_restaurant['restaurant_pizzas'] = [
        {
            'id': resturant_pizza.id,
            'pizza': resturant_pizza.pizza.to_dict(only=('id', 'name', 'ingredients')),
            'pizza_id': resturant_pizza.pizza_id,
            'price': resturant_pizza.price,
            'restaurant_id': resturant_pizza.restaurant_id
        }
        for resturant_pizza in restaurant.restaurant_pizzas
    ]
    
    return jsonify(serialized_restaurant)

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    # Deleteing associated RestaurantPizza instances
    for resturant_pizza in restaurant.restaurant_pizzas:
        db.session.delete(resturant_pizza)
    
    # Deleteing the Restaurant
    db.session.delete(restaurant)
    db.session.commit()
    
    return '', 204

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    # adding the pizzas to a dictionary
    pizzas_dict = [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in pizzas]
    return jsonify(pizzas_dict)

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    # Checking if pizza and restaurant exist
    pizza = Pizza.query.get(data['pizza_id'])
    restaurant = Restaurant.query.get(data['restaurant_id'])
    if not pizza or not restaurant:
        return jsonify({'error': 'Pizza or Restaurant not found'}), 404

    # Checking for an existing association
    existing_resturantPizza = RestaurantPizza.query.filter_by(
        pizza_id=data['pizza_id'], restaurant_id=data['restaurant_id']).first()
    if existing_resturantPizza:
        return jsonify({'error': 'RestaurantPizza already exists'}), 409

    #Checking the price range
    if data['price'] < 1 or data['price'] > 30:
        return jsonify({'errors': ['validation errors']}), 400

    # Create new RestaurantPizza instance
    restaurant_pizza = RestaurantPizza(
        price=data['price'], pizza_id=data['pizza_id'], restaurant_id=data['restaurant_id'])

    db.session.add(restaurant_pizza)
    db.session.commit()

    resturant_pizza_dict = restaurant_pizza.to_dict(('id', 'price', 'pizza_id', 'restaurant_id'))

    # Adding pizza details in the response
    resturant_pizza_dict['pizza'] = pizza.to_dict(('id', 'name', 'ingredients'))
    resturant_pizza_dict['restaurant'] = restaurant.to_dict(('id', 'name', 'address'))

    return jsonify(resturant_pizza_dict), 201

@app.route('/')
def index():
    return '<h1>Code challenge</h1>'


if __name__ == '__main__':
    app.run(port=5555, debug=True)
