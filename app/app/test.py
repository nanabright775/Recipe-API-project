"""sample test"""


from django.test import SimpleTestCase

from app import calc

class CalcTests(SimpleTestCase):
    def test_add_numbers(self):
        """test to add two giving numbers"""
        res = calc.add(5, 7)
        
        self.assertEqual(res, 12)
        
        
    def test_substract_numbers(self):
        """subtracting numbers"""
        res = calc.substats(45, 0)
        
        self.assertEqual(res, 45)
        