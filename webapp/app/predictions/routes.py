from app.predictions import blueprint
from flask import request, render_template
from flask_login import login_required


@blueprint.route('/<template>')
@login_required
def route_template(template, methods=['GET']):
    
    
    # if request.method == 'GET':
    #     print("!"*100)
    #     #sensors = structure.Sensor.query.all()
    #     #print(sensors)
    #     print("!"*100)

    if template == "melmodel":
        return render_template(template + '.html')
    
    else: return render_template(template + '.html')
