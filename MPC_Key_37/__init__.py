"""Original MPC Key 37 adapter for Ableton Live 12 (Python 3)."""


def create_instance(c_instance):
    from .surface import MPCKey37
    return MPCKey37(c_instance=c_instance)
