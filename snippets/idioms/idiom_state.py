"""C habit versus Python idiom: a state machine. Run: python3 idiom_state.py"""

from collections.abc import Callable
from enum import Enum, auto


def step_c_style(state: int, event: str) -> int:
    """States are integers 0..3, and the logic is a nest of tests, like switch inside switch."""
    IDLE, ARMED, RUNNING, FAULT = range(4)
    if state == IDLE:
        if event == "arm":
            return ARMED
    elif state == ARMED:
        if event == "start":
            return RUNNING
        elif event == "disarm":
            return IDLE
        elif event == "fault":
            return FAULT
    elif state == RUNNING:
        if event == "stop":
            return IDLE
        elif event == "fault":
            return FAULT
    elif state == FAULT:
        if event == "reset":
            return IDLE
    return state  # an event that does not apply is ignored


class State(Enum):
    IDLE = auto()
    ARMED = auto()
    RUNNING = auto()
    FAULT = auto()


TRANSITIONS: dict[tuple[State, str], State] = {
    (State.IDLE, "arm"): State.ARMED,
    (State.ARMED, "start"): State.RUNNING,
    (State.ARMED, "disarm"): State.IDLE,
    (State.ARMED, "fault"): State.FAULT,
    (State.RUNNING, "stop"): State.IDLE,
    (State.RUNNING, "fault"): State.FAULT,
    (State.FAULT, "reset"): State.IDLE,
}

ON_ENTRY: dict[State, Callable[[], str]] = {
    State.IDLE: lambda: "output off",
    State.ARMED: lambda: "ready to start",
    State.RUNNING: lambda: "output enabled",
    State.FAULT: lambda: "output disabled, fault latched",
}


def step_pythonic(state: State, event: str) -> State:
    return TRANSITIONS.get((state, event), state)


events = ["start", "arm", "start", "fault", "start", "reset", "arm", "disarm"]
c_state, state = 0, State.IDLE
for event in events:
    c_state = step_c_style(c_state, event)
    new = step_pythonic(state, event)
    action = ON_ENTRY[new]() if new is not state and new in ON_ENTRY else ""
    note = "ignored" if new is state else action
    print(f"{event:7} -> {new.name:8} {note}")
    assert State(c_state + 1) is new  # the same machine, checked at every step
    state = new

reachable = {State.IDLE}
while True:  # data can be inspected: which states can be reached from IDLE?
    more = {t for (s, _), t in TRANSITIONS.items() if s in reachable} - reachable
    if not more:
        break
    reachable |= more
print("reachable from IDLE:", sorted(s.name for s in reachable))
print(
    "states with no way out:",
    sorted(s.name for s in State if not any(k[0] is s for k in TRANSITIONS)) or "none",
)
