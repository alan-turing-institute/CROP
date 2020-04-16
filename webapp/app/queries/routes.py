from app.queries import blueprint
from flask_login import login_required

from __app__.crop.structure import SQLA as db


@blueprint.route('/getallsensors', methods=['GET'])
@login_required
def get_all():


    # db.session.

    return "THIS IS THE RESULT OF THE QUERY"