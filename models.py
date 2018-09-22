from dao.firestore_tool import *


class Test(Collection):
    a = AssistFieldClass(int, True)
    b = AssistFieldClass(str, True)

