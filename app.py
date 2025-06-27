import streamlit as st
import requests
import time

# Configure page
st.set_page_config(
    page_title="AI Booking Agent",
    page_icon="📅",
    layout="wide"
)

st.title("📅 AI Booking Agent")
st.markdown("*Natural language appointment scheduling powered by AI*")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm your AI booking assistant. I can help you schedule appointments, check availability, and manage your calendar. What would you like to do today?"
        }
    ]

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = f"conv_{int(time.time())}"

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "https://scheduler-3-165s.onrender.com/chat",  # ✅ use your deployed backend URL
                    json={
                        "message": prompt,
                        "conversation_id": st.session_state.conversation_id
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data.get("response", "I'm sorry, I couldn't process that request.")
                    st.markdown(assistant_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })

                    if data.get("booking_confirmed"):
                        st.success("✅ Appointment booked successfully!")
                        booking_details = data.get("booking_details", {})
                        if booking_details:
                            st.info(f"**Booking Details:**\n"
                                    f"- Date: {booking_details.get('date', 'N/A')}\n"
                                    f"- Time: {booking_details.get('time', 'N/A')}\n"
                                    f"- Duration: {booking_details.get('duration', 'N/A')} minutes")
                else:
                    error_msg = "Sorry, I'm having trouble connecting to my booking system. Please try again."
                    st.markdown(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

            except requests.exceptions.RequestException:
                error_msg = "I'm experiencing some technical difficulties. Please try again in a moment."
                st.markdown(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Sidebar
with st.sidebar:
    st.header("💡 Tips")
    st.markdown("""
    **What I can help you with:**
    - Schedule new appointments
    - Check availability
    - Find suitable time slots
    - Confirm bookings

    **Example requests:**
    - "I need to book a meeting tomorrow afternoon"
    - "Do you have any free time this Friday?"
    - "Schedule a 30-minute call next week"
    - "What's available between 2–4 PM on Monday?"
    """)

    st.header("🔄 Actions")
    if st.button("Clear Chat History"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI booking assistant. I can help you schedule appointments, check availability, and manage your calendar. What would you like to do today?"
            }
        ]
        st.session_state.conversation_id = f"conv_{int(time.time())}"
        st.rerun()
