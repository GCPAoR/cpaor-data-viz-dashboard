import os

import streamlit.components.v1 as components

build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/build"))

_component_func = components.declare_component(
    "ga_component",
    path=build_dir,
)


def inject_google_analytics(measurement_id: str, key=None):
    return _component_func(measurementId=measurement_id, key=key)
