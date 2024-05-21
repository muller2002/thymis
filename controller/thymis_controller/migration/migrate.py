from packaging import version
from thymis_controller.migration.to_0_0_2 import to_0_0_2
from thymis_controller.migration.to_0_0_3 import to_0_0_3
from thymis_controller.migration.to_0_0_4 import to_0_0_4

KNOWN_VERSIONS = [
    "0.0.1",
    "0.0.2",
    "0.0.3",
    "0.0.4",
]  # TODO: remove this, replace with dynamic versioning


def migrate(state: dict):
    assert state["version"] in KNOWN_VERSIONS, f"Unknown version {state['version']}"

    if version.parse(state["version"]) == version.parse("0.0.1"):
        state = to_0_0_2(state)

    if version.parse(state["version"]) == version.parse("0.0.2"):
        state = to_0_0_3(state)

    if version.parse(state["version"]) == version.parse("0.0.3"):
        state = to_0_0_4(state)

    return state
