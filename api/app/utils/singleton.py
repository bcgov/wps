""" Singleton utility class for creating a single instance of something """


class Singleton:
    """ Non thread-safe singleton decorator.
        Stolen from: https://stackoverflow.com/a/7346105
    """

    def __init__(self, decorated):
        self._decorated = decorated
        self._instance = None

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.
        """
        # NOTE: Code use to attempt to return self._instance, and if an exception was thrown,
        # would then call self._decorated to instantiate. This can result in logging of exceptions which
        # can get confusing. Nice to first check if it's set, and if not - try to make it.
        if self._instance is None:
            self._instance = self._decorated()
        return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
