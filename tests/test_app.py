import unittest
import json
import os
import sys

# Ensure repository root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_public_base_url
import database

class HoneyChainTestSuite(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_pwa_manifest(self):
        res = self.client.get('/manifest.json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/manifest+json', res.content_type)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data.get('short_name'), 'HoneyChain')
        self.assertEqual(data.get('display'), 'standalone')

    def test_service_worker(self):
        res = self.client.get('/sw.js')
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/javascript', res.content_type)
        content = res.data.decode('utf-8')
        self.assertIn('CACHE_NAME', content)

    def test_offline_page(self):
        res = self.client.get('/offline')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Offline', res.data)

    def test_portal_home(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.data.decode('utf-8')
        self.assertIn('/manifest.json', content)
        self.assertIn('viewport', content)

    def test_login_flow(self):
        res = self.client.get('/login', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Authenticate with seeded beekeeper persona
        login_res = self.client.post('/login', data={
            'identifier': 'beekeeper',
            'password': 'beekeeper123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Welcome back', login_res.data)

    def test_role_switcher(self):
        res = self.client.get('/switch-role/lab', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Switched active session to', res.data)

    def test_traceability(self):
        res = self.client.get('/trace/HC-2026-9842', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        content = res.data.decode('utf-8')
        self.assertIn('HC-2026-9842', content)

    def test_blockchain_verification_api(self):
        res = self.client.get('/api/verify-chain')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn('verified', data)
        self.assertTrue(data['verified'])

    def test_chain_api(self):
        res = self.client.get('/api/chain')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertTrue(data['is_chain_valid'])
        self.assertTrue(data['length'] >= 1)

    def test_public_url_resolution(self):
        with app.test_request_context('/', headers={'Host': 'testserver.com'}):
            url = get_public_base_url()
            self.assertFalse(url.endswith('/'))
            self.assertTrue(url.startswith('http'))

if __name__ == '__main__':
    unittest.main()
