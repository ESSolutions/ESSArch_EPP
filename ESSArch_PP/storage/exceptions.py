class TapeDriveLockedError(Exception):
    """The tape drive is locked"""
    pass

class TapeMountedAndLockedByOtherError(Exception):
    """The tape is mounted and locked by another process"""
    pass

class TapeMountedError(Exception):
    """The tape is already mounted"""
    pass


class TapeUnmountedError(Exception):
    """The tape is already unmounted"""
    pass
