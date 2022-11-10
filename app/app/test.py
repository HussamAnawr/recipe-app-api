

from django.test import SimpleTestCase
from . import calc

class CalcTest(SimpleTestCase):
    
    def test_add_number(self):
        res = calc.add(1,3)
        self.assertEqual(res, 4)

    def test_sub_numbers(self):
        res = calc.sub(10, 15)
        self.assertEqual(res, 5)