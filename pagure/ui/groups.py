# -*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import flask
import os

from sqlalchemy.exc import SQLAlchemyError

import pagure
import pagure.forms
import pagure.lib


# pylint: disable=E1101

# URLs

@pagure.APP.route('/groups')
def group_lists():
    ''' List all the groups associated with all the projects. '''
    groups = pagure.lib.search_groups(pagure.SESSION, group_type='user')

    group_types = ['user']
    if pagure.is_admin():
        group_types = [
            grp.group_type
            for grp in pagure.lib.get_group_types(pagure.SESSION)
        ]
        # Make sure the admin type is always the last one
        group_types.remove('admin')
        group_types.append('admin')

    form = pagure.forms.NewGroupForm(group_types=group_types)

    return flask.render_template(
        'group_list.html',
        groups=groups,
        form=form,
    )


@pagure.APP.route('/group/<group>', methods=['GET', 'POST'])
def view_group(group):
    ''' Displays information about this group. '''
    group = pagure.lib.search_groups(
        pagure.SESSION, group_name=group, group_type='user')

    if not group:
        flask.abort(404, 'Group not found')

    # Add new user to the group if asked
    form = pagure.forms.AddUserForm()
    if pagure.authenticated() and form.validate_on_submit():

        username = form.user.data

        try:
            msg = pagure.lib.add_user_to_group(
                pagure.SESSION,
                username=username,
                group=group,
                user=flask.g.fas_user.username,
                admin=pagure.is_admin(),
            )
            pagure.SESSION.commit()
            flask.flash(msg)
        except pagure.exceptions.PagureException, err:
            SESSION.rollback()
            flask.flash(err.message, 'error')
            return flask.redirect(
                flask.url_for('.view_group', group=group.group_name))
        except SQLAlchemyError as err:
            pagure.SESSION.rollback()
            flask.flash(
                'Could not add user `%s` to group `%s`.' % (
                    user.user, group.group_name),
                'error')
            pagure.APP.logger.debug(
                'Could not add user `%s` to group `%s`.' % (
                    user.user, group.group_name))
            pagure.APP.logger.exception(err)


    return flask.render_template(
        'group_info.html',
        group=group,
        form=form,
    )


@pagure.APP.route('/group/<group>/<user>/delete', methods=['POST'])
@pagure.cla_required
def group_user_delete(user, group):
    """ Delete an user from a certain group
    """
    form = pagure.forms.ConfirmationForm()
    if form.validate_on_submit():

        try:
            pagure.lib.delete_user_of_group(
                pagure.SESSION,
                username=user,
                groupname=group,
                user=flask.g.fas_user.username,
                is_admin=pagure.is_admin()
            )
            pagure.SESSION.commit()
            flask.flash(
                'User `%s` removed from the group `%s`' % (user, group))
        except pagure.exceptions.PagureException, err:
            pagure.SESSION.rollback()
            flask.flash(err.message, 'error')
            return flask.redirect(
                flask.url_for('.view_group', group=group))
        except SQLAlchemyError as err:
            pagure.SESSION.rollback()
            flask.flash(
                'Could not remove user `%s` from the group `%s`.' % (
                    user.user, group),
                'error')
            pagure.APP.logger.debug(
                'Could not remove user `%s` from the group `%s`.' % (
                    user.user, group))
            pagure.APP.logger.exception(err)

    return flask.redirect(flask.url_for('.view_group', group=group))


@pagure.APP.route('/group/<group>/delete', methods=['POST'])
@pagure.cla_required
def group_delete(group):
    """ Delete a certain group
    """
    # Add new user to the group if asked
    form = pagure.forms.ConfirmationForm()
    if form.validate_on_submit():
        group_obj = pagure.lib.search_groups(
            pagure.SESSION, group_name=group)

        if not group_obj:
            flask.flash('No group `%s` found' % group, 'error')
            return flask.redirect(flask.url_for('.group_lists'))

        pagure.SESSION.delete(group_obj)

        pagure.SESSION.commit()
        flask.flash(
            'Group `%s` has been deleted' % (group))

    return flask.redirect(flask.url_for('.group_lists'))


@pagure.APP.route('/group/add', methods=['GET', 'POST'])
@pagure.cla_required
def add_group():
    """ Endpoint to create groups
    """
    user = pagure.lib.search_user(
        pagure.SESSION, username=flask.g.fas_user.username)
    if not user:  # pragma: no cover
        return flask.abort(403)

    group_types = ['user']
    if pagure.is_admin():
        group_types = [
            grp.group_type
            for grp in pagure.lib.get_group_types(pagure.SESSION)
        ]
        # Make sure the admin type is always the last one
        group_types.remove('admin')
        group_types.append('admin')

    form = pagure.forms.NewGroupForm(group_types=group_types)

    if not pagure.is_admin():
        form.group_type.data = 'user'

    if form.validate_on_submit():

        try:
            msg = pagure.lib.add_group(
                session=pagure.SESSION,
                group_name=form.group_name.data,
                group_type=form.group_type.data,
                user=flask.g.fas_user.username,
                is_admin=pagure.is_admin(),
            )
            pagure.SESSION.commit()
            flask.flash('Group `%s` created.' % grp.group_name)
            flask.flash(msg)
            return flask.redirect(flask.url_for('.group_lists'))
        except SQLAlchemyError as err:
            pagure.SESSION.rollback()
            flask.flash('Could not create group.')
            pagure.APP.logger.debug('Could not create group.')
            pagure.APP.logger.exception(err)

    return flask.render_template(
        'add_group.html',
        form=form,
    )