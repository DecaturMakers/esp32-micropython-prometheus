"""Quick hack to avoid import errors since micropython doesn't have typing"""

TYPE_CHECKING = False


class Dict:
    pass


class List:
    pass


class Optional:
    pass


class Union:
    pass


class Tuple:
    pass
