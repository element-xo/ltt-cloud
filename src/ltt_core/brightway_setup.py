import brightway2 as bw

from .config import get_settings


def setup_brightway(base_dir=None):
    """Initialise Brightway with the configured project name.

    The project name comes from the BRIGHTWAY_PROJECT env var.
    In Docker/Kubernetes the data directory should be mounted at
    /data/brightway (set BRIGHTWAY2_DIR accordingly).
    """
    settings = get_settings()
    if not bw.projects:
        bw.projects.set_current(settings.BRIGHTWAY_PROJECT)