"""
views for the Template Value Set data object
"""
import logging
from flask import render_template, url_for, redirect, request, flash
from sqlalchemy.exc import IntegrityError
from app import app, db
from app.models import TemplateValueSet, ConfigTemplate
from app.forms import TemplateValueSetForm
from config import ROOT_URL

logger = logging.getLogger()


@app.route(ROOT_URL + "template/<int:config_template_id>/valueset/<int:template_value_set_id>/")
def view_template_value_set(config_template_id, template_value_set_id):
    """view a single Template Value Set

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    return render_template(
        "template_value_set/view_template_value_set.html",
        config_template=config_template,
        template_value_set=TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()
    )


@app.route(ROOT_URL + "template/<int:config_template_id>/valueset/add", methods=["GET", "POST"])
@app.route(ROOT_URL + "template/<int:config_template_id>/valueset/<int:template_value_set_id>/edit", methods=["GET",
                                                                                                              "POST"])
def edit_template_value_set(config_template_id, template_value_set_id=None):
    """edit/add a new Template Value Set

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    parent_config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    if template_value_set_id:
        template_value_set = TemplateValueSet.query.get(template_value_set_id)

    else:
        template_value_set = None

    form = TemplateValueSetForm(request.form, template_value_set)

    if form.validate_on_submit():
        try:
            created = False
            if not template_value_set:
                template_value_set = TemplateValueSet(hostname="", config_template=parent_config_template)
                created = True

            form.populate_obj(template_value_set)

            template_value_set.config_template = parent_config_template
            template_value_set.copy_variables_from_config_template()

            # update variable data
            if not created:
                for key in template_value_set.get_template_value_names():
                    template_value_set.update_variable_value(var_name=key, value=request.form["edit_" + key])

                # hostname is always the same as the name of the template value set
                template_value_set.update_variable_value(var_name="hostname", value=template_value_set.hostname)

            db.session.add(template_value_set)
            db.session.commit()

            if created:
                flash("Template value set successful created", "success")

            else:
                flash("Template value set template successful saved", "success")

            return redirect(url_for(
                "view_config_template",
                project_id=parent_config_template.project.id,
                config_template_id=parent_config_template.id
            ))

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "name already exist, please use another one"
                flash(msg, "error")

            else:
                msg = "Template Value set was not created (unknown error)"
                flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Template Value set was not created (unknown error)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")

    return render_template(
        "template_value_set/edit_template_value_set.html",
        config_template=parent_config_template,
        template_value_set=template_value_set,
        form=form
    )


@app.route(ROOT_URL + "template/<int:config_template_id>/valueset/<int:template_value_set_id>/delete", methods=["GET",
                                                                                                                "POST"])
def delete_template_value_set(config_template_id, template_value_set_id):
    """delete the Config Template

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_value_set = TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()

    if request.method == "POST":
        # drop record and add message
        try:
            db.session.delete(template_value_set)
            db.session.commit()

        except:
            flash("Config Template %s was not deleted" % template_value_set.hostname, "error")

        flash("Config Template %s successful deleted" % template_value_set.hostname, "success")
        return redirect(
            url_for(
                "view_config_template",
                project_id=config_template.project.id,
                config_template_id=template_value_set.config_template.id
            )
        )

    return render_template(
        "template_value_set/delete_template_value_set.html",
        template_value_set=template_value_set
    )
