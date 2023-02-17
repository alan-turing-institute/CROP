from bcrypt import checkpw

from os import environ

from flask import jsonify, render_template, redirect, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import login_manager

from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm

from cropcore.structure import SQLA as db
from cropcore.structure import UserClass
from cropcore import utils


@blueprint.route("/")
def route_default():
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/<template>")
@login_required
def route_template(template):
    return render_template(template + ".html")


@blueprint.route("/fixed_<template>")
@login_required
def route_fixed_template(template):
    return render_template("fixed/fixed_{}.html".format(template))


@blueprint.route("/page_<error>")
def route_errors(error):
    return render_template("errors/page_{}.html".format(error))


## Login & Registration


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if "login" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        user = UserClass.query.filter_by(username=username).first()
        if user and checkpw(password.encode("utf8"), user.password):
            login_user(user)
            return redirect(url_for("base_blueprint.route_default"))
        return render_template("errors/page_403.html")

    if not current_user.is_authenticated:
        return render_template(
            "login/login.html",
            login_form=login_form,
            create_account_form=create_account_form,
            disable_register=(environ.get("CROP_DISABLE_REGISTER", "True") == "True"),
        )
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/create_user", methods=["POST"])
@login_required
def create_user():
    success, result = utils.create_user(**request.form)
    return jsonify({"success": success, "output": result})


@blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/shutdown")
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."


# Errors


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("base_blueprint.login"))


@blueprint.errorhandler(403)
def access_forbidden(error):
    return redirect(url_for("base_blueprint.login"))


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("errors/page_404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("errors/page_500.html"), 500
