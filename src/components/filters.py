from __future__ import annotations

import streamlit as st
from src.bot.chatbot import chatbot as ask_bot, stream_chatbot


def render_filters_sidebar() -> None:
    """Render common sidebar filters shared across pages.

    Keys ensure the widgets are stateful across pages.
    """
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("public/images/user.png", width=36)
    with col2:
        st.markdown("**" + getattr(st.user, "name", "") + "**")

    st.title("Filters")
    st.selectbox("Segment", ["Placeholder", "Placeholder", "Placeholder", "Placeholder"], key="Placeholder")
    st.date_input("Start date", key="start_date")
    st.date_input("End date", key="end_date")


    #log out button
    if st.button("Log out"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.logout()


    st.divider()
    st.subheader("Chat with your data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display conversation history using chat bubbles
    user_avatar = None
    user_obj = getattr(st, "user", None)
    if user_obj:
        if isinstance(user_obj, dict):
            user_avatar = user_obj.get("picture")
        else:
            user_avatar = getattr(user_obj, "picture", None)

    for message in st.session_state.chat_history:
        role = "user" if message.get("role") == "user" else "assistant"
        avatar = user_avatar if role == "user" else None
        with st.chat_message(role, avatar=avatar):
            st.markdown(message.get("content", ""))

    user_prompt = st.text_area("Ask a question", key="chatbot_prompt", height=80)
    col_send, col_clear = st.columns(2)
    with col_send:
        send_clicked = st.button("Send", key="chatbot_send")
    with col_clear:
        clear_clicked = st.button("Clear", key="chatbot_clear")

    if clear_clicked:
        st.session_state.chat_history = []
        st.rerun()

    if send_clicked and user_prompt and user_prompt.strip():
        cleaned_prompt = user_prompt.strip()

        # Build lightweight context from current filters
        segment = st.session_state.get("Placeholder")
        start_date = st.session_state.get("start_date")
        end_date = st.session_state.get("end_date")
        system_context = (
            f"Current Filters -> Segment: {segment}; Start: {start_date}; End: {end_date}. "
            "Use these as context when answering."
        )

        # Append and immediately echo user's message bubble
        st.session_state.chat_history.append({"role": "user", "content": cleaned_prompt})
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(cleaned_prompt)

        # Stream assistant reply
        full_text = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                for chunk in stream_chatbot(
                    cleaned_prompt,
                    history=st.session_state.chat_history,
                    system_context=system_context,
                ):
                    full_text += chunk
                    placeholder.markdown(full_text)
            except Exception as error:
                full_text = f"Sorry, I couldn't get a response right now: {error}"
                placeholder.markdown(full_text)

        # Save assistant response and trim history length
        st.session_state.chat_history.append({"role": "assistant", "content": full_text})
        if len(st.session_state.chat_history) > 50:
            st.session_state.chat_history = st.session_state.chat_history[-50:]
        st.rerun()