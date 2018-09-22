from dao.firestore_tool import *


class Test(Collection):
    a = AssistFieldClass(int)
    b = AssistFieldClass(str)


a = Test()
a.a = 10
a.b = "123123"
a.commit()