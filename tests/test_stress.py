import unittest
import sys
from unittest.mock import MagicMock, patch
import json
import time
import os

# Mock mysql.connector before importing app because app.py has global init_db()
sys.modules['mysql.connector'] = MagicMock()

# Now we can safely import app
import app

class StressTestTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True
        # Reset state
        app.is_stressing = False

    def tearDown(self):
        # Ensure stress is stopped
        app.is_stressing = False

    def test_stress_flow(self):
        # 1. Start Stress Test
        response = self.app.post('/stress/start', 
                                 data=json.dumps({'cpu_load': True}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Stress test started')
        self.assertTrue(app.is_stressing)

        # 2. Try to start again (should fail)
        response = self.app.post('/stress/start', 
                                 data=json.dumps({'cpu_load': True}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Stress test already running')

        # 3. Stop Stress Test
        response = self.app.post('/stress/stop')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Stress test stopped')
        self.assertFalse(app.is_stressing)

if __name__ == '__main__':
    unittest.main()
