#!/usr/bin/env python

def _pickle_method(method):
    """
        Utility function for the reduction of a Python method. This is
        for pickling (serialization) purposes.
        See https://docs.python.org/2/library/copy_reg.html.
        Arguments:
            method: The function to be reduced.
        Returns:
            a Tuple representing the method
    """
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    """
        Utility function to reconstruct a method from the arguments. This
        is for unpickling (de-serialization) purposes.
        See https://docs.python.org/2/library/copy_reg.html
        Arguments:
            func_name: Function name
            obj: Object name
            cls: Class name
        Returns:
            a Python method
    """
    try:
        for acls in cls.mro():
            try:
                func = acls.__dict__[func_name]
            except KeyError:
                pass
            else:
                break
    except AttributeError:
        func = cls.__dict__[func_name]
    return func.__get__(obj, cls)
