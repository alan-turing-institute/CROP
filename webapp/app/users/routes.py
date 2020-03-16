from app.users import blueprint
from flask import render_template, request, jsonify
from flask_login import login_required

from app.base.models import User

@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):

    if request.method == 'GET':

        print("!"*100)

        users = User.query.all()

        # users_json = jsonify([u.serialize() for u in users])

        # print(users_json)

        print("!"*100)

        return render_template(template + '.html', users=users)

    
