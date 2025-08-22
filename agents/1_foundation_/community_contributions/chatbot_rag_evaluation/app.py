import gradio as gr
from controller import ChatbotController


controller = ChatbotController()
with gr.Blocks() as demo:
    chat = gr.Chatbot(type="messages", min_height=600, label="Assistant")
    msg = gr.Textbox(label="Your message", placeholder="Want to know more about Damla’s work? Type your question here...")

    history_state = gr.State([])   
    processed_emails_state = gr.State([])

    def respond(user_msg, history, recorded_emails_state):
        history.append({"role":"user", "content":user_msg})
        reply, emails = controller.get_response(message=user_msg, history=history, recorded_emails=set(recorded_emails_state))
        history.append({"role":"assistant", "content":reply})

        return history, history, list(emails)

    msg.submit(respond, inputs=[msg, history_state, processed_emails_state], outputs=[chat, history_state, processed_emails_state])
    msg.submit(lambda: "", None, msg)

demo.launch(inbrowser=True)