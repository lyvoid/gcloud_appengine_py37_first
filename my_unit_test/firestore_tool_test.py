import unittest

from dao.firestore_tool import *


class TestMongoTool(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_error_column(self):
        """
        测试在column定义不是AssistColumnClass时候是否正确抛出异常
        :return:
        """
        with self.assertRaises(FireStoreAssistInitialException):
            class ErrorColumn(Collection):
                __collection__ = 'test'
                id = AssistFieldClass('123')

            u = ErrorColumn()
            u.id = 123

    def test_error_type_(self):
        """
        测试column加入限制以后，是否能正确检测出错误
        :return:
        """
        with self.assertRaises(FireStoreTypeNotMatchException):
            class ErrorType(Collection):
                __table__ = 'test'
                id = AssistFieldClass(int)

            u = ErrorType()
            u.id = '123'

    def test_normal(self):
        """
        测试常规通过情况
        :return:
        """

        class TestClass(Collection):
            __table__ = 'test'
            id = AssistFieldClass(int)
            str_value = AssistFieldClass(str)
            normal_value = AssistFieldClass()

        u = TestClass()
        u.id = 1
        u.str_value = '1'
        u.normal_value = 1
        u.commit()
        u.delete()
        u.id = 1
        u.str_value = '1'
        u.normal_value = 1
        u.commit()
        u.normal_value = '1'
        u.commit()
        u = TestClass()
        u.id = 1

        self.assertEqual(u.normal_value, '1')
        self.assertEqual(u.str_value, '1')
        u.delete()
        u.id = 1
        self.assertEqual(u.load(), False)
        self.assertEqual(u.str_value, None)


if __name__ == '__main__':
    unittest.main()
