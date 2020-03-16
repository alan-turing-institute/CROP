from app.sensors import blueprint
from flask import render_template
from flask_login import login_required

from flask import request

# from crop.structure import db
# from crop.structure import 

@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):
    
    
    if request.method == 'GET':
        print("!"*100)
        #sensors = structure.Sensor.query.all()
        #print(sensors)
        print("!"*100)
   

    return render_template(template + '.html')
