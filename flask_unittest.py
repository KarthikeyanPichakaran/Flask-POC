import unittest
import requests
import json
from app import app

class TestFlaskpoc(unittest.TestCase):
    def test_login(self):
        with app.test_client(self) as c:
            with c.session_transaction() as sess:
                sess['cust_id'] = 'aid'
                sess['_fresh'] = True
            resp = c.get('/')
            response = resp.status_code
            self.assertEqual(response, 200)
        
    def test_get_customer_details(self):
        tester = app.test_client(self)
        resp = tester.get("/custdata")
        self.assertEqual(resp.content_type, 'application/json')

    def test_add_customer(self):
        tester = app.test_client()
        resp = tester.get("/custdata/17")
        self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    unittest.main()