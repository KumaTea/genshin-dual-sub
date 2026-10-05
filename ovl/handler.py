from fmt.ruby import Segment
from ovl.session import overlay


def ovl_handler(segments: list[Segment]) -> None:
    overlay.set_segments(segments)


def clear_subtitle() -> None:
    overlay.set_segments([])
