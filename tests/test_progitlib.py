#-*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

__requires__ = ['SQLAlchemy >= 0.8']
import pkg_resources

import unittest
import sys
import os

from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import progit.lib
import tests


class ProgitLibtests(tests.Modeltests):
    """ Tests for progit.lib """

    def test_get_next_id(self):
        """ Test the get_next_id function of progit.lib. """
        tests.create_projects(self.session)
        self.assertEqual(1, progit.lib.get_next_id(self.session, 1))

    def test_search_user_all(self):
        """ Test the search_user of progit.lib. """

        # Retrieve all users
        items = progit.lib.search_user(self.session)
        self.assertEqual(2, len(items))
        self.assertEqual(1, items[0].id)
        self.assertEqual('pingou', items[0].user)
        self.assertEqual('pingou', items[0].username)
        self.assertEqual([], items[0].groups)
        self.assertEqual(2, items[1].id)
        self.assertEqual('foo', items[1].user)
        self.assertEqual('foo', items[1].username)
        self.assertEqual([], items[1].groups)

    def test_search_user_username(self):
        """ Test the search_user of progit.lib. """

        # Retrieve user by username
        item = progit.lib.search_user(self.session, username='foo')
        self.assertEqual('foo', item.user)
        self.assertEqual('foo', item.username)
        self.assertEqual([], item.groups)

        item = progit.lib.search_user(self.session, username='bar')
        self.assertEqual(None, item)

    def test_search_user_email(self):
        """ Test the search_user of progit.lib. """

        # Retrieve user by email
        item = progit.lib.search_user(self.session, email='foo@foo.com')
        self.assertEqual(None, item)

        item = progit.lib.search_user(self.session, email='foo@bar.com')
        self.assertEqual('foo', item.user)
        self.assertEqual('foo', item.username)
        self.assertEqual([], item.groups)
        self.assertEqual(
            ['foo@bar.com'], [email.email for email in item.emails])

        item = progit.lib.search_user(self.session, email='foo@pingou.com')
        self.assertEqual('pingou', item.user)
        self.assertEqual(
            ['bar@pingou.com', 'foo@pingou.com'],
            [email.email for email in item.emails])

    def test_search_user_token(self):
        """ Test the search_user of progit.lib. """

        # Retrieve user by token
        item = progit.lib.search_user(self.session, token='aaa')
        self.assertEqual(None, item)

        item = progit.lib.model.User(
            user='pingou2',
            fullname='PY C',
            token='aaabbb',
        )
        self.session.add(item)
        self.session.commit()

        item = progit.lib.search_user(self.session, token='aaabbb')
        self.assertEqual('pingou2', item.user)
        self.assertEqual('PY C', item.fullname)

    def test_search_user_pattern(self):
        """ Test the search_user of progit.lib. """

        # Retrieve user by pattern
        item = progit.lib.search_user(self.session, pattern='a*')
        self.assertEqual([], item)

        item = progit.lib.model.User(
            user='pingou2',
            fullname='PY C',
            token='aaabbb',
        )
        self.session.add(item)
        self.session.commit()

        items = progit.lib.search_user(self.session, pattern='p*')
        self.assertEqual(2, len(items))
        self.assertEqual(1, items[0].id)
        self.assertEqual('pingou', items[0].user)
        self.assertEqual('pingou', items[0].username)
        self.assertEqual([], items[0].groups)
        self.assertEqual(
            ['bar@pingou.com', 'foo@pingou.com'],
            [email.email for email in items[0].emails])
        self.assertEqual(3, items[1].id)
        self.assertEqual('pingou2', items[1].user)
        self.assertEqual('pingou2', items[1].username)
        self.assertEqual([], items[1].groups)
        self.assertEqual(
            [], [email.email for email in items[1].emails])

    @patch('progit.lib.git.update_git_ticket')
    @patch('progit.lib.notify.send_email')
    def test_new_issue(self, p_send_email, p_ugt):
        """ Test the new_issue of progit.lib. """
        p_send_email.return_value = True
        p_ugt.return_value = True

        tests.create_projects(self.session)
        repo = progit.lib.get_project(self.session, 'test')

        # Before
        issues = progit.lib.search_issues(self.session, repo)
        self.assertEqual(len(issues), 0)

        # See where it fails
        self.assertRaises(
            progit.exceptions.ProgitException,
            progit.lib.new_issue,
            session=self.session,
            repo=repo,
            title='Test issue',
            content='We should work on this',
            user='blah',
            ticketfolder=None
        )

        # Create issues to play with
        msg = progit.lib.new_issue(
            session=self.session,
            repo=repo,
            title='Test issue',
            content='We should work on this',
            user='pingou',
            ticketfolder=None
        )
        self.session.commit()
        self.assertEqual(msg, 'Issue created')

        msg = progit.lib.new_issue(
            session=self.session,
            repo=repo,
            title='Test issue',
            content='We should work on this',
            user='foo',
            ticketfolder=None
        )
        self.session.commit()
        self.assertEqual(msg, 'Issue created')

        # After
        issues = progit.lib.search_issues(self.session, repo)
        self.assertEqual(len(issues), 2)

    @patch('progit.lib.git.update_git_ticket')
    @patch('progit.lib.notify.send_email')
    def test_edit_issue(self, p_send_email, p_ugt):
        """ Test the edit_issue of progit.lib. """
        p_send_email.return_value = True
        p_ugt.return_value = True

        self.test_new_issue()
        repo = progit.lib.get_project(self.session, 'test')
        issue = progit.lib.search_issues(self.session, repo, issueid=2)

        # Edit the issue
        msg = progit.lib.edit_issue(
            session=self.session,
            issue=issue,
            ticketfolder=None,
            status='Invalid')
        self.session.commit()
        self.assertEqual(msg, 'Edited successfully issue #2')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ProgitLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
