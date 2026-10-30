"""Drop-in banner for SGPayPulse Streamlit.
Place assets/ beside this file, then import render_banner from the main app.
"""
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"

def render_banner(animated: bool = True) -> None:
    """Display the Singapore-themed banner with a gentle animated GIF option."""
    filename = "sgpaypulse_banner_animated.gif" if animated else "sgpaypulse_banner.png"
    st.image(str(ASSETS / filename), use_container_width=True)
