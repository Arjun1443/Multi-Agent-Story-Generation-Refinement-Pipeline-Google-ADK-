import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi_app.main import app, UnusableOutput
from fastapi_app.workflow import run_story


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_approval_stops_without_refining(self):
        generate = AsyncMock(side_effect=['draft', 'APPROVED'])
        result = await run_story('idea', 'Mystery', 'Hopeful', 3, generate)
        self.assertTrue(result['approved'])
        self.assertEqual(generate.await_count, 2)
        self.assertEqual(result['story'], 'draft')

    async def test_final_revision_is_reviewed(self):
        generate = AsyncMock(side_effect=['draft', 'fix ending', 'revised', 'APPROVED'])
        result = await run_story('idea', 'Mystery', 'Hopeful', 1, generate)
        self.assertEqual(result['refinements'], 1)
        self.assertEqual(result['history'][-1]['story'], 'revised')
        self.assertTrue(result['approved'])

    async def test_bounded_loop_and_exact_approval(self):
        generate = AsyncMock(side_effect=['draft', 'Not APPROVED', 'revision', 'APPROVED with changes'])
        result = await run_story('idea', 'Mystery', 'Hopeful', 1, generate)
        self.assertFalse(result['approved'])
        self.assertEqual(generate.await_count, 4)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_home_and_health(self):
        self.assertIn('Storycraft Studio', self.client.get('/').text)
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/docs').status_code, 200)

    def test_validation(self):
        for body in ({'premise': ' '}, {'premise': 'a', 'max_refinements': 4},
                     {'premise': 'a', 'max_refinements': True}, {'premise': 'a', 'unexpected': 1}):
            self.assertEqual(self.client.post('/api/stories', json=body).status_code, 422)

    def test_missing_key(self):
        with patch.dict('os.environ', {'GOOGLE_API_KEY': ''}):
            self.assertEqual(self.client.post('/api/stories', json={'premise': 'idea'}).status_code, 503)

    def test_success(self):
        result = dict(draft='draft', story='final', approved=True, refinements=1,
                      history=[dict(round=1, story='final', critique='APPROVED')])
        with patch('fastapi_app.main.generate_story', AsyncMock(return_value=result)):
            response = self.client.post('/api/stories', json={'premise': 'idea'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['story'], 'final')

    def test_provider_errors_are_redacted(self):
        for error, status in [(Exception('secret-key-in-provider-url'), 502),
                              (TimeoutError(), 504), (UnusableOutput(), 502)]:
            with patch('fastapi_app.main.generate_story', AsyncMock(side_effect=error)):
                response = self.client.post('/api/stories', json={'premise': 'idea'})
            self.assertEqual(response.status_code, status)
            self.assertNotIn('secret-key', response.text)
