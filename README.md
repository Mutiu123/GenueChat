
### Project Overview

**GenueChat** is an AI chatbot application designed to deliver enhanced performance and context-aware responses. It utilises **Retrieval-Augmented Generation (RAG)**, combining retrieval-based and generative approaches to provide accurate and contextually relevant responses. The chatbot is implemented with **LangChain** and **Groq**, and features a user-friendly frontend built with **Gradio**. The purpose of this project is to create a versatile and efficient chatbot capable of handling complex queries and providing valuable insights from various data sources, including PDF documents.

### Technical Details

**Architecture**: The architecture of **GenueChat** is built around **LangChain** for natural language processing and Groq for efficient and scalable model serving. The backend handles the retrieval and generation of responses, while the frontend, built with **Gradio**, provides an intuitive interface for user interaction.

**RAG Implementation: Retrieval-Augmented Generation (RAG)** enhances the **chatbot’s** performance by combining the strengths of retrieval-based and generative models. This approach allows the chatbot to fetch relevant information from a large dataset and generate coherent and contextually appropriate responses, improving both accuracy and relevance.

**Frontend:** The frontend is developed using **Gradio**, which offers a user-friendly web interface. This makes it easy for users to interact with the chatbot, submit queries, and receive responses in a seamless manner.

### Business Impact:

**GenueChat** can significantly benefit the employer’s business by improving customer service, increasing operational efficiency, and providing valuable insights from data. Its ability to handle complex queries and provide accurate information can enhance user experience and support decision-making processes.



### Challenges and Solutions

**Challenges**: During the development process, we faced challenges such as optimizing the RAG model for performance, ensuring seamless integration of various technologies, and handling large PDF documents efficiently.

**Solutions**: To overcome these challenges, we implemented performance tuning techniques, conducted extensive testing, and utilized scalable infrastructure with Groq. We also developed custom preprocessing pipelines for handling PDF content effectively.

**Scalability**: GenueChat is designed to be scalable and adaptable for other applications. The use of Docker for containerization ensures that the application can be easily deployed and scaled across different environments. Future enhancements could include expanding the dataset, integrating additional data sources, and improving the chatbot’s natural language understanding capabilities.

Would you like to explore any specific part of this presentation in more detail?

## **System Demo:**

![The System Demo](https://github.com/Mutiu123/Medical-Insurence-Premium-prediction-System/blob/main/demos/demo1.png)


### Prerequisites

- Python 3.8 or later
- Docker (optional, for containerization)
- Groq setup for model serving
- Gradio for the frontend interface
- Langchain

## **To run the model**
1. **Clone the Repository**:
   - First, clone the project repository to your local machine. You can do this using Git or by downloading the ZIP file from the repository.

2. **Install Dependencies**:
   - Open your terminal or command prompt and navigate to the project directory.
   - Install the necessary Python libraries mentioned in the `requirements.txt` file using the following command:
     ```
     pip install -r requirements.txt
     ```

3. **Run the Project App**:
   - In the same terminal or command prompt, execute the following command to run the Streamlight app:
     ```
     run python app.py
     ```
   - This will start the local development server, and you'll see a message indicating that the app is running.
   - Open your web browser and visit 'http://0.0.0.0:3000/' (or the URL provided in the terminal) to access the interactive web app.

4. **Conversation**:
   - On the app, you may upload a PDF file and ask a question to get an answer, or ask a question directly.
   - After entering your question, click the “Submit” button.


**Access the Deployed App**:
   - Visit the following link: [GenueChat](https://a7f923d8262b8dd3d4.gradio.live).
   - You'll see the web interface where users can input patient information and get predictions.
