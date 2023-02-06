from flask import render_template, request
from flask_login import login_required


from app.users import blueprint
from cropcore.structure import SQLA as db
from cropcore.structure import UserClass
from cropcore import utils


@blueprint.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if request.method == "POST":
        user_id = request.values.get("user_id")
        user = db.session.get(UserClass, user_id)
        db.session.delete(user)
        db.session.commit()
    users = UserClass.query.all()
    return render_template("users.html", users=users)


@blueprint.route("/create_user_form", methods=["GET", "POST"])
@login_required
def create_user_form():
    if request.method == "GET":
        message = None
    elif request.method == "POST":
        success, result = utils.create_user(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
        )
        if success:
            message = f"Created new user (ID = {result})."
        else:
            message = f"Failed to create new user. Error: {result}"
    else:
        message = f"Unknown HTTP method {request.method}"
    return render_template("create_user_form.html", message=message)
