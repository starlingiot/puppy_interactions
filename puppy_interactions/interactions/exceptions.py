class UnrecognizedCommandException(Exception):
    """When the text passed doesn't resolve to an unambiguous command"""
    pass


class CheaterException(Exception):
    """When someone tries to rate themselves"""
    pass
