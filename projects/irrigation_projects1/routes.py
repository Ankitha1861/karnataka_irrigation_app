from flask import Blueprint
from projects.app_original import show_dashboard

irrigation1_bp = Blueprint('irrigation1', __name__)

@irrigation1_bp.route('/irrigation1')
def irrigation1():
    return show_dashboard('projects/irrigation_projects1/data/karnataka_irr1.xlsx')


