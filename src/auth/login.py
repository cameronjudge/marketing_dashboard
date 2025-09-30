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

    # Center all content using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Center the image using columns
        img_col1, img_col2, img_col3 = st.columns([1, 1, 1])
        with img_col2:
            st.image('https://framerusercontent.com/assets/3nUMjfjekVFLnxccSGqCnKJY8.png', width=300)
        
        # Center the title and subtitle
        st.markdown("<h1 style='text-align: center'>Judge.me Marketing Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center'>Please sign in to continue.</h3>", unsafe_allow_html=True)
        
        # Center the login button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            if st.button('Login with Google', use_container_width=True):
                st.login('google')

    return False
