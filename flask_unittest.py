import unittest
import requests
import json
from app import app

url = 'http://127.0.0.1:5000/'
test_data = {'account_type':'saving', 'address':'tvmalai', 'bank_name': 'sbi', 'contact':723543, 'name':'rajiv'}
post_data = {'account_type':'demat', 'address':'thane', 'bank_name': 'boa', 'contact':234, 'name':'selva'}
to_update = {'customer_id': 20, 'account_type':'demat', 'address':'thane', 'bank_name': 'bankofamerica', 'contact':234, 'name':'selva'}

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
        self.assertAlmostEquals(resp.content_type, 'application/json')

    def test_single_customer(self):
        tester = app.test_client()
        resp = tester.get("/custdata/17")
        self.assertEqual(resp.status_code, 200)

    def test_add(self):
        response = requests.post(f'{url}custdata', json=post_data)
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        response = requests.put(f'{url}custdata/20', json=to_update)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        response = requests.delete(f'{url}custdata/21')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()