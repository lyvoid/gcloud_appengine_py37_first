# -*- coding:utf-8-*-
import logging
from google.cloud import firestore
import google
from dao.dao_exception import *

_db = firestore.Client()
_collections = {}


class AssistFieldClass:
    """
    该类用于在申明collection时作为辅助列
    """

    def __init__(self, type_=None, is_not_none=False):
        if type_ is not None:
            if type(type_) is not type:
                raise FireStoreAssistInitialException('type_ must be a `type`, such as `int`')
        self.type_ = type_
        self.is_not_none = is_not_none


class CollectionMeta(type):
    """
    collection的metaclass，自动将其子类中定义的AssistColumnClass删除，
    同时将将__collection__替换成对应的db.collection对象连接
    如果此前已有连接，则采用此前的连接
    如果此前不存在连接，则新建一个连接
    """

    def __new__(mcs, name, bases, attrs):
        """
        该方法在发现新的类以该class作为metaclass时运行，运行时间晚于新
        类中的类代码（写在类中，但不在方法内的代码）
        :param name:类的名字
        :param bases:类的基类
        :param attrs:类的类属性（除了自己定义的外，还有一些自有的类属性）
        :return:
        """
        if name == 'Collection':
            return type.__new__(mcs, name, bases, attrs)
        # connect collection to attrs['collection']
        collection_name = attrs.get('__collection__', None) or name
        if collection_name not in _collections:
            _collections[collection_name] = _db.collection(collection_name)
        attrs['__collection__'] = _collections[collection_name]
        attrs['__collection_name__'] = collection_name
        attrs['__type_map__'] = {}
        attrs['__is_not_none__'] = []

        # delete all assist attr
        tmp = []
        for k, v in attrs.items():
            if isinstance(v, AssistFieldClass):
                tmp.append(k)

        for k in tmp:
            if attrs[k].type_ is not None:
                # 如果辅助类中定义了类型的话，就把类型记下来，
                # 方便之后做限制
                attrs['__type_map__'][k] = attrs[k].type_
            if attrs[k].is_not_none:
                attrs['__is_not_none__'].append(k)
            attrs.pop(k)

        return type.__new__(mcs, name, bases, attrs)


class Collection(metaclass=CollectionMeta):
    """
    有新的Collection（collection）时，继承该类，
    需要定义__collection__为表名
    如有需要可以用AssistColumnClass来定义一些辅助列

    所有的数据存储在__data__中
    __collection__会被替换成db.collection
    """

    def __init__(self, document_name=None):
        self.__data__ = {}
        # document reference
        self.__document__ = None
        self.__document_name__ = document_name
        self.load()

    def __getattr__(self, key):
        # if key.startswith('__'):
        #     return self.__dict__.get(key)
        # 上面两步其实没有必要，因为默认会先调用自建的__getattribute__
        # 从__dict__中取值，然后从类变量中取值
        # 如果都找不到最后才会走这个方法
        return self.__data__.get(key)

    def __setattr__(self, key, value):
        if key.startswith('__'):
            self.__dict__[key] = value
        else:
            if key in self.__type_map__ and type(value) is not self.__type_map__[key]:
                # 如果写了类型限制，但当前赋值类型与限制类型不同，抛出Exception
                raise FireStoreTypeNotMatchException(
                    'type not match in collection `%s`, at key `%s`,'
                    'require type: `%s`,'
                    'get type: `%s`' % (
                        self.__collection_name__,
                        key,
                        str(self.__type_map__[key]),
                        type(value)
                    )
                )
            self.__data__[key] = value

    def load(self):
        if self.document_name is None:
            self.__document__ = self.__collection__.document()
        else:
            self.__document__ = self.__collection__.document(self.document_name)
            try:
                doc = self.__document__.get()
                self.__data__ = doc.to_dict()
                return True
            except google.cloud.exceptions.NotFound:
                print('No such document `%s`!' % self.__document_name__)
                return False

    def load_by_data(self):
        self.__document__ = self._find(self.__data__, row=1)[0]
        self.__data__ = self.__document__.to_dict()
        self.__document_name__ = self.__document__.id

    def commit(self, is_merge=False):
        if self.__document__ is None:
            logging.warning('need load `__document__` before commit')
            return False

        if self.__data__ is None:
            logging.warning('can not commit to firestore since date is None')
            return False

        for key in self.__is_not_none__:
            if key not in self.__data__:
                logging.warning('%s can not be none' % key)
                return False

        if is_merge:
            self.__document__.update(
                self.__data__,
                firestore.CreateIfMissingOption(True)
            )
        else:
            self.__document__.set(self.__data__)
        self.__document_name__ = self.__document__.id
        return True

    def delete(self):
        if self.__document__ is None:
            logging.warning('need load `__document__` before delete')
            return
        self.__document__.delete()
        self.__document__ = None
        self.__document_name__ = None

    def delete_all(self, batch_size=50, one_time_delete=100):
        docs = self.__collection__.limit(one_time_delete).get()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted = deleted + 1
        if deleted >= batch_size:
            return self.delete_all(batch_size)

    def _find(self, keys: dict, row=None, order_by=None):
        wheres = []
        for k, v in keys.items():
            wheres.append([k, '==', v])
        return self._where(wheres, row, order_by)

    def find(self, keys: dict, row=None, order_by=None):
        return [x.to_dict() for x in self.find(keys, row, order_by)]

    def _where(self, wheres=None, row=None, order_by=None):
        """
        :param order_by: 按什么来排序
        :param wheres: [[u'population', u'>', 2500000]]
        :param row: 行数，如果没有定义end的时候有效
        :return: 如果都是None的话，就返回所有的内容（返回类型为[{}]）
        """
        data = self.__collection__
        if wheres is not None:
            for w in wheres:
                data = data.where(*w)
        if order_by is not None:
            data = data.order_by(order_by)
        if row is not None:
            data = data.limit(row)
        docs = data.get()
        return docs

    def where(self, wheres=None, row=None, order_by=None):
        return [x.to_dict() for x in self._where(wheres, row, order_by)]

    def insert_many(self, data: list, document_names=None):
        batch = _db.batch()
        for i in range(len(data)):
            if document_names is not None:
                batch.set(self.__collection__.document(
                    document_names[i]
                ), data[i])
            else:
                batch.set(self.__collection__.document(), data[i])
        batch.commit()
