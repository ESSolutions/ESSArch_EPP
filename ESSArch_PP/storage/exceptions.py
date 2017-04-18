class TapeMountedAndLockedByOtherError(Exception):
    """The tape is mounted and locked by another process"""
    pass

class TapeMountedError(Exception):
    """The tape is already mounted"""
    pass
