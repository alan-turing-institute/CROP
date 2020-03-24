from app.users import blueprint
from flask import render_template, request, jsonify
from flask_login import login_required

#from app.base.models import User

# from crop.structure import db
from crop.structure import UserClass


@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):

    if request.method == 'GET':

        users = UserClass.query.all()

        return render_template(template + '.html', users=users)

    
