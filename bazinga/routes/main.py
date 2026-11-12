from functools import wraps

from flask import Blueprint, abort, jsonify, redirect, render_template, session, url_for

from ..extensions import db
from ..models import User

def get_current_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return user if user and user.is_active else None

main_bp = Blueprint("main", __name__)

MODULES = {
    "competitions": {
        "eyebrow": "CENTRAL DE TORNEIOS / 01",
        "title": "CAMPEONATOS",
        "subtitle": "Encontre sua próxima disputa.",
        "description": "Os torneios oficiais do Ultimate Bazinga Championship serão publicados aqui, com regras, formato, inscrições e calendário.",
        "empty_title": "A próxima disputa está sendo preparada.",
        "empty_description": "Ainda não há campeonatos publicados. Quando um organizador abrir inscrições, você encontrará aqui o formato, as vagas e as datas.",
        "icon": "♜",
        "status": "AGUARDANDO TORNEIOS",
    },
    "matches": {
        "eyebrow": "CENTRAL DE PARTIDAS / 02",
        "title": "PARTIDAS",
        "subtitle": "Cada confronto escreve uma história.",
        "description": "Acompanhe partidas agendadas, resultados confirmados e confrontos em andamento.",
        "empty_title": "Nenhum confronto agendado.",
        "empty_description": "Quando os torneios gerarem suas partidas, os horários, participantes e resultados aparecerão nesta página.",
        "icon": "⚔",
        "status": "SEM PARTIDAS",
    },
    "ranking": {
        "eyebrow": "CLASSIFICAÇÃO GLOBAL / 03",
        "title": "RANKING",
        "subtitle": "O topo não se conquista sozinho.",
        "description": "Classificações oficiais por temporada, jogo e modalidade.",
        "empty_title": "A corrida pelo topo ainda não começou.",
        "empty_description": "Os pontos e posições serão calculados a partir dos resultados oficiais. Nenhuma classificação fictícia será exibida.",
        "icon": "♛",
        "status": "RANKING AINDA NÃO INICIADO",
    },
    "achievements": {
        "eyebrow": "LEGADO DOS COMPETIDORES / 04",
        "title": "CONQUISTAS",
        "subtitle": "Grandes momentos merecem ser lembrados.",
        "description": "Veja títulos, marcos, recordes e reconhecimentos conquistados dentro do campeonato.",
        "empty_title": "Seu mural de conquistas está vazio por enquanto.",
        "empty_description": "Títulos e medalhas serão adicionados automaticamente conforme os resultados forem homologados.",
        "icon": "✧",
        "status": "CONQUISTAS EM BREVE",
    },
    "community": {
        "eyebrow": "BAZINGA HUB / 05",
        "title": "COMUNIDADE",
        "subtitle": "Rivais hoje. Lendas amanhã.",
        "description": "Conheça outros competidores, encontre equipes e acompanhe as novidades da comunidade.",
        "empty_title": "A comunidade está se reunindo.",
        "empty_description": "Perfis públicos, equipes e recursos sociais serão liberados em uma próxima etapa.",
        "icon": "♧",
        "status": "COMUNIDADE EM PREPARAÇÃO",
    },
}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("main.championship_home", screen="auth"))
        return view(*args, **kwargs)
    return wrapped


@main_bp.get("/")
def championship_home():
    return render_template("championship.html")


@main_bp.get("/hub")
@login_required
def hub():
    return redirect(url_for("main.championship_home"))


@main_bp.get("/<module>")
@login_required
def module_page(module):
    data = MODULES.get(module)
    if not data:
        abort(404)
    return render_template("module.html", module=data, module_key=module)


@main_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "ultimate-bazinga-championship"})
