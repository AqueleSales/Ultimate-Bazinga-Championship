from flask import Blueprint, jsonify, render_template

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def championship_home():
    return render_template("championship.html")


@main_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "ultimate-bazinga-championship"})
