from mirror.agents.state import ExerciseState


def start_router(state: ExerciseState) -> str:
    if state.get("error"):
        return "end"
    return "select_excerpt"


def generic_router(next_step: str):
    def _router(state: ExerciseState) -> str:
        if state.get("error"):
            return "end"
        return next_step

    return _router


def route_after_verify(state: ExerciseState) -> str:
    if not state.get("error"):
        return "end"

    retry_count = state.get("retry_count", 0)
    if retry_count >= 1:
        return "end"

    return "build_repair_prompt"
