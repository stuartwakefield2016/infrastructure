def around(before, after):

    def decorator(fn):

        def wrapper(*args, **kwargs):
            before(*args, **kwargs)
            result = fn(*args, **kwargs)
            after(*args, **kwargs)
            return result

        return wrapper

    return decorator
