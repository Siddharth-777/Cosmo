import os
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from elevenlabs.client import ElevenLabs
from langdetect import detect
from datetime import datetime

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
if not elevenlabs_api_key:
    raise ValueError("ELEVENLABS_API_KEY not found in environment variables. Please check your .env file.")

# Initialize LLM
try:
    llm = ChatGroq(
        temperature=0.7,
        model_name="llama3-8b-8192",
        groq_api_key=groq_api_key
    )
    print("LLM initialized successfully")
except Exception as e:
    raise RuntimeError(f"Failed to initialize ChatGroq: {e}")

# Define multilingual prompt
prompt = PromptTemplate(
    input_variables=["history", "input", "language"],
    template=""" 
You are Cosmo, an AI therapist designed to sound like a real, human therapist—warm, mature, and emotionally intelligent. You respond in a calm, grounded, and supportive tone.

The user has input text in {language}. Respond in the same language as the user's input (English or Hindi). Keep replies short, natural, and human—just like a therapist in a real conversation. Be empathetic without overexplaining. Avoid sounding robotic, scripted, or overly formal.

Your tone should be:
- Supportive, but never overwhelming
- Calm and caring, without being clinical
- Conversational, not preachy
- Curious and reflective, not analytical

Always:
- Acknowledge what the user is feeling ("That sounds tough." / "यह मुश्किल लगता है।")
- Ask simple, open-ended follow-ups ("Do you want to talk more about it?" / "क्या आप इसके बारे में और बात करना चाहते हैं?")
- Validate feelings without assuming or fixing ("It’s okay to feel that way." / "ऐसा महसूस करना ठीक है।")
- Leave space for the user to open up

Avoid:
- Long or detailed replies
- Giving advice unless asked
- Talking about yourself or how you were built
- Sounding like a chatbot or AI

Here’s the conversation so far:
{history}

User: {input}
Cosmo:
"""
)

# Initialize message history and chain
history = ChatMessageHistory()
chain = prompt | llm
chatbot = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="input",
    history_messages_key="history"
)

# Initialize ElevenLabs client
try:
    client = ElevenLabs(api_key=elevenlabs_api_key)
    print("ElevenLabs client initialized successfully")
except Exception as e:
    raise RuntimeError(f"Failed to initialize ElevenLabs client: {e}")

def get_chat_history():
    messages = []
    for i in range(0, len(history.messages), 2):
        if i + 1 < len(history.messages):
            user_timestamp = history.messages[i].additional_kwargs.get('timestamp', datetime.now())
            chat = {
                'date': user_timestamp.strftime('%Y-%m-%d'),
                'preview': f"You: {history.messages[i].content[:50]}..." if len(history.messages[i].content) > 50
                else f"You: {history.messages[i].content}",
                'full_conversation': {
                    'user': history.messages[i].content,
                    'bot': history.messages[i + 1].content
                }
            }
            messages.append(chat)

    if not messages:
        messages.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'preview': "No conversations yet",
            'full_conversation': None
        })

    return messages

def run(user_input):
    if not user_input or not isinstance(user_input, str):
        print("Invalid input provided")
        return {"text": "Please provide a valid message.", "audio_url": None}

    try:
        # Attempt language detection with fallback
        detected_lang = detect(user_input) if user_input.strip() else "en"
        language = "Hindi" if detected_lang == "hi" else "English"
        print(f"Detected language: {language}")

        history.add_user_message(user_input)
        history.messages[-1].additional_kwargs['timestamp'] = datetime.now()

        result = chatbot.invoke(
            {"input": user_input, "language": language},
            config={"configurable": {"session_id": "default_session"}}
        )
        text_response = result.content if hasattr(result, "content") else str(result)
        if not text_response or not isinstance(text_response, str):
            text_response = "Sorry, I didn’t catch that." if language == "English" else "क्षमा करें, मैं समझ नहीं पाया।"
        print(f"Text response: {text_response}")

        history.add_ai_message(text_response)
        history.messages[-1].additional_kwargs['timestamp'] = datetime.now()

        try:
            voice = "Rachel" if language == "English" else "Kanika - Relatable Hindi Voice"
            audio_generator = client.generate(
                text=text_response,
                voice=voice,
                model="eleven_multilingual_v2" if language == "Hindi" else "eleven_monolingual_v1"
            )
            audio_bytes = b"".join(audio_generator)
            print(f"Audio generated successfully for: {text_response}")
        except Exception as audio_error:
            print(f"Audio generation error: {audio_error}")
            return {"text": text_response, "audio_url": None}

        audio_path = os.path.join("static", "response.mp3")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        print(f"Audio saved to: {audio_path}")

        return {"text": text_response, "audio_url": f"/static/response.mp3"}

    except Exception as e:
        print(f"Error in run: {e}")
        fallback_text = "Sorry, I couldn’t process that." if detect(user_input) != "hi" else "क्षमा करें, मैं इसे प्रोसेस नहीं कर सका।"
        return {"text": fallback_text, "audio_url": None}

if __name__ == "__main__":
    # Test the setup
    print("Testing run function with sample input")
    test_response = run("Hello, I feel sad.")
    print(f"Test response: {test_response}")