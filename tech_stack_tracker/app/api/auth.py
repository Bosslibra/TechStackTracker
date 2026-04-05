from flask import Blueprint, jsonify, render_template, request

auth_bp = Blueprint("auth", __name__)

# TODO: implement login, logout, status