import unittest
from evaluator import safe_eval

class C(object):
    def __init__(self):
        self.v = 20
        self.open = open
        self.secretx = None

    def set_x(self, value):
        self.secretx = value

class EvaluateShould(unittest.TestCase):
    def test_evaluate1plus1(self):
        result, _ = safe_eval('1+1')
        self.assertEqual([2], result)
    def test_moduleVars(self):
        _, env = safe_eval("""x = 200""")
        self.assertEqual(200, env.lookup('x'))
    def test_addonefunction(self):
        _, env = safe_eval("""
def add1(x):
    return x + 1""")
        self.assertIsNotNone(env.lookup('add1'))
        result = env.lookup('add1').call(1)
        self.assertEqual(2, result)
    def test_support_local_variables(self):
        _, env = safe_eval("""
def add1(x):
    y = 101
    return x + y""")
        self.assertIsNotNone(env.lookup('add1'))
        result = env.lookup('add1').call(1)
        self.assertEqual(102, result)
    def test_modify_python_vals(self):
        _, env = safe_eval("""
def modify(obj):
    obj.open = obj.v
""")
        c = C()
        env.lookup('modify').call(c)
        self.assertEqual(c.open, 20)
    def test_not_write_python_functions(self):
        _, env = safe_eval("""
def modify(obj):
    obj.v = obj.open
""")
        c = C()
        env.lookup('modify').call(c)
        self.assertNotEqual(c.v, open)
    def test_use_setters_automatically(self):
        _, env = safe_eval("""
def modify(obj):
    obj.x = 2000
""")
        c = C()
        env.lookup('modify').call(c)
        self.assertEqual(c.secretx, 2000)


if __name__ == '__main__':
    unittest.main()
