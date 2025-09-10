import streamlit as st

with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def user_login() -> bool:
    """Render login UI and return True when the user is authenticated.

    This function does not call st.stop(); callers should gate content
    rendering based on the boolean it returns.
    """

    # Guard against environments where st.user may not be available 
    user_obj = getattr(st, "user", None)
    is_logged_in = bool(user_obj and getattr(user_obj, "is_logged_in", False))

    if is_logged_in:
        return True

    left, center, right = st.columns([1, 1, 1])
    with center:
        st.markdown("""
            <div class="login-container">
                <img src="https://framerusercontent.com/assets/3nUMjfjekVFLnxccSGqCnKJY8.png" alt="Judge.me Logo" class="logo-image">
                <h1 class="login-title">Marketing Dashboard</h1>
                <p class="login-subtitle">Please sign in to continue.</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button('Login with Google'):
            st.login('google')

    return False
