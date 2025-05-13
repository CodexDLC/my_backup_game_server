import sys
sys.path.append("/opt/new_order_rpg/")
from preview_module.preview_routes import preview
from flask import Blueprint, jsonify, render_template, request
import os
from database.world_system_utils import DatabaseUtils

import logging

# Настройка логирования
logger = logging.getLogger('WebsiteMain')
logger.setLevel(logging.DEBUG)



# Настроить подключение к базе данных
db = DatabaseUtils(
    db_name=os.getenv("DB_NAME"),
    db_user=os.getenv("DB_USER"),
    db_password=os.getenv("DB_PASSWORD"),
    db_host=os.getenv("DB_HOST"),
    db_port=int(os.getenv("DB_PORT", 5432))
)
db.connect()

# 🔹 Blueprint базы знаний
knowledge = Blueprint('knowledge', __name__, url_prefix='/knowledge-base')

@knowledge.route('/')
def get_knowledge_base():
    weapons = db.fetch_data("weapon_templates", ["full_name", "color", "effect_description"])
    armor = db.fetch_data("armor_templates", ["template_name", "color", "effect_description"])
    accessories = db.fetch_data("accessory_templates", ["full_name", "color", "effect_description"])

    return jsonify({
        "weapons": [{"name": i[0], "color": i[1], "description": i[2]} for i in weapons],
        "armor": [{"name": i[0], "color": i[1], "description": i[2]} for i in armor],
        "accessories": [{"name": i[0], "color": i[1], "description": i[2]} for i in accessories]
    })

@knowledge.route('/get_database_menu')
def get_database_menu():
    return jsonify([
        {"id": "weapons", "name": "Оружие"},
        {"id": "armor", "name": "Броня"},
        {"id": "accessories", "name": "Аксессуары"}
    ])

from flask import render_template  # ← убедись, что это есть в начале файла

@knowledge.route("/settings")
def settings_page():
    return render_template("settings.html")

# 🔹 Регистрация всех маршрутов
def register_routes(app):
    app.register_blueprint(knowledge)
    app.register_blueprint(preview)
