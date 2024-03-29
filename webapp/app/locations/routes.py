from app.locations import blueprint
from flask_login import login_required
from flask import request, render_template
from sqlalchemy import exc


from cropcore.structure import SQLA as db
from cropcore.structure import LocationClass


CONST_ACTION_ADD = "Add"
CONST_ACTION_EDIT = "Edit"

CONST_FORM_ACTION_SUBMIT = "submit"
CONST_FORM_ACTION_CANCEL = "cancel"
CONST_FORM_ACTION_DELETE = "delete"


@blueprint.route("/<template>", methods=["POST", "GET"])
@login_required
def route_template(template):

    if template == "locations":
        locations = LocationClass.query.all()
        return render_template(template + ".html", locations=locations)

    elif template == "location_form":

        if request.method == "GET":

            loc_id = request.args.get("query")

            if loc_id is not None:
                action = CONST_ACTION_EDIT
                location = LocationClass.query.filter_by(id=loc_id).first()
            else:
                action = CONST_ACTION_ADD
                location = None

            if location == None:
                location = LocationClass(None, None, "", "")

            return render_template(
                template + ".html",
                action=action,
                location=location,
                loc_id=loc_id,
            )

        elif request.method == "POST":

            if request.form["action_button"] == CONST_FORM_ACTION_SUBMIT:

                loc_action = request.form.get("loc_action")

                loc_zone = request.form.get("loc_zone")
                loc_aisle = request.form.get("loc_aisle")
                loc_column = request.form.get("loc_column")
                loc_shelf = request.form.get("loc_shelf")
                loc_aisle = None if loc_aisle == "" else loc_aisle
                loc_column = None if loc_column == "" else loc_column
                loc_shelf = None if loc_shelf == "" else loc_shelf

                # Adding a new location
                if loc_action == CONST_ACTION_ADD:
                    try:
                        location = LocationClass(
                            zone=loc_zone,
                            aisle=loc_aisle,
                            column=loc_column,
                            shelf=loc_shelf,
                        )

                        db.session.add(location)
                        db.session.commit()

                        # Only after the commit the id property is set
                        loc_message = "New location (ID = {}) has been added.".format(
                            location.id
                        )

                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        loc_message = str(e)

                # Modifying an existing location
                elif loc_action == CONST_ACTION_EDIT:
                    loc_id = request.form.get("loc_id")

                    if loc_id is not None:

                        LocationClass.query.filter_by(id=loc_id).update(
                            dict(
                                zone=loc_zone,
                                aisle=loc_aisle,
                                column=loc_column,
                                shelf=loc_shelf,
                            )
                        )
                        try:
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            raise e

                        loc_message = "Location (ID = {}) has been updated.".format(
                            loc_id
                        )
                    else:
                        loc_message = "Unknown location cannnot be updated."

            elif request.form["action_button"] == CONST_FORM_ACTION_DELETE:

                loc_id = request.form.get("loc_id")

                if loc_id is not None:

                    LocationClass.query.filter_by(id=loc_id).delete()
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        raise e

                    loc_message = "Location (ID = {}) has been deleted.".format(loc_id)
                else:
                    loc_message = "Unknown location cannnot be deleted."

            elif request.form["action_button"] == CONST_FORM_ACTION_CANCEL:
                loc_message = ""

            locations = LocationClass.query.all()

            # TODO: redirect
            return render_template(
                "locations.html", locations=locations, loc_message=loc_message
            )
