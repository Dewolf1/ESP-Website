import json

from unittest.mock import patch

from django.test import TestCase, RequestFactory

from esp.program.models import ClassSubject
from esp.program.tests import ProgramFrameworkTest
from esp.tagdict.models import Tag
from esp.random.views import good_random_class, main, ajax


class GoodRandomClassTest(ProgramFrameworkTest):

    def test_returns_class_subject_no_constraints(self):
        Tag.setTag('random_constraints', value='{}')
        result = good_random_class()
        self.assertIsInstance(result, ClassSubject)
        Tag.unSetTag('random_constraints')

    def test_empty_constraints(self):
        Tag.setTag('random_constraints', value='{}')
        result = good_random_class()
        self.assertIsInstance(result, ClassSubject)
        Tag.unSetTag('random_constraints')

    def test_filters_bad_program_names(self):
        # all our test classes belong to 'TestProgram' so
        # filtering it out should leave nothing
        constraints = json.dumps({'bad_program_names': ['TestProgram']})
        Tag.setTag('random_constraints', value=constraints)
        with self.assertRaises(Exception):
            good_random_class()
        Tag.unSetTag('random_constraints')

    def test_filters_bad_titles(self):
        first_class = ClassSubject.objects.filter(
            status__gte=0, parent_program=self.program
        ).first()
        constraints = json.dumps({'bad_titles': [first_class.title]})
        Tag.setTag('random_constraints', value=constraints)
        # run a bunch of times to make sure the filterd class never shows up
        for _ in range(20):
            result = good_random_class()
            self.assertNotEqual(result.title, first_class.title)
        Tag.unSetTag('random_constraints')

    def test_filters_combined(self):
        first_class = ClassSubject.objects.filter(
            status__gte=0, parent_program=self.program
        ).first()
        constraints = json.dumps({
            'bad_program_names': ['SomeOtherProgram'],
            'bad_titles': [first_class.title],
        })
        Tag.setTag('random_constraints', value=constraints)
        # SomeOtherProgram wont match so only the title filter applys
        for _ in range(20):
            result = good_random_class()
            self.assertNotEqual(result.title, first_class.title)
        Tag.unSetTag('random_constraints')

    def test_bad_program_names_partial_match(self):
        # 'Test' is a substring of 'TestProgram', icontains should catch it
        constraints = json.dumps({'bad_program_names': ['Test']})
        Tag.setTag('random_constraints', value=constraints)
        with self.assertRaises(Exception):
            good_random_class()
        Tag.unSetTag('random_constraints')


class RandomViewTest(ProgramFrameworkTest):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        Tag.setTag('random_constraints', value='{}')

    def tearDown(self):
        Tag.unSetTag('random_constraints')
        super().tearDown()

    def test_main_view_status_200(self):
        response = self.client.get('/random/')
        self.assertEqual(response.status_code, 200)

    def test_ajax_view_returns_json(self):
        response = self.client.get('/random/ajax')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('title', data)
        self.assertIn('program', data)
        self.assertIn('info', data)

    def test_ajax_view_values_nonempty(self):
        response = self.client.get('/random/ajax')
        data = json.loads(response.content)
        self.assertTrue(len(data['title']) > 0)
        self.assertTrue(len(data['program']) > 0)
