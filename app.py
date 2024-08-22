from src.llm import handle_chat
import gradio as gr
import os

# Gradio interface
ui = gr.Interface(
    fn=handle_chat,
    inputs=[gr.File(), 'text'],
    outputs=gr.Textbox(lines=14),
    title="GenueChat",
    description="Upload a PDF file and ask a question to get an answer, \n\
        or ask a question directly.",
    theme=gr.themes.Default(primary_hue="violet", secondary_hue="violet")
)

port = int(os.environ.get("PORT", 3000))
ui.launch(server_name="0.0.0.0", server_port=port,share=True)
