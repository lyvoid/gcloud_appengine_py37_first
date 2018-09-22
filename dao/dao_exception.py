class FireStoreTypeNotMatchException(Exception):

    def __init__(self, *args):
        super(FireStoreTypeNotMatchException, self).__init__(*args)


class FireStoreAssistInitialException(Exception):
    def __init__(self, *args):
        super(FireStoreAssistInitialException, self).__init__(*args)


class LoadWithoutDocNameException(Exception):
    def __init__(self, *args):
        super(LoadWithoutDocNameException, self).__init__(*args)
