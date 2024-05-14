from flask import Flask, Response, request, json, render_template, redirect,jsonify, url_for
from logging import INFO
import os
from azure.communication.callautomation import (
    CallAutomationClient,
    CallConnectionClient,
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource, FileSource)
from azure.core.messaging import CloudEvent
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
from prompts import *

load_dotenv()

AZURE_OPENAI_ENDPOINT= os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")

# Your ACS resource connection string
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")

# Your ACS resource phone number will act as source number to start outbound call
ACS_PHONE_NUMBER = os.getenv("ACS_PHONE_NUMBER")


# Callback events URI to handle callback events.
CALLBACK_URI_HOST = os.getenv("CALLBACK_URI_HOST")
CALLBACK_EVENTS_URI = CALLBACK_URI_HOST + os.getenv("CALLBACK_EVENTS_URI") 
COGNITIVE_SERVICES_ENDPOINT = os.getenv("COGNITIVE_SERVICES_ENDPOINT")


TEMPLATE_FILES_PATH = os.getenv("TEMPLATE_FILES_PATH") # default is "templates"

# Prompts for text to speech
NO_RESPONSE = "I didn't receive an input, a human agent will contact you again. Goodbye"
INVALID_AUDIO = "I'm sorry, I didn't understand your response, please try again."
RETRY_CONTEXT = "retry"
TEXT_TO_PLAY_WHILE_WAITING="AI is processing, please wait"

#keep track the counter for the memory after streamed
MEMORY_COUNT_THAT_STREAMED = 0

call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)


app = Flask(__name__,
            template_folder=TEMPLATE_FILES_PATH)

# store each session's data, use other database for production
session_db = {}

languages = {

    # "stt": "en-SG",
    # "tts": "en-US-AvaMultilingualNeural", #en-SG-LunaNeural",

    "stt": "zh-CN",
    "tts": "zh-CN-XiaoxiaoMultilingualNeural", #"zh-CN-XiaoyanNeural", 

    # "stt": "ms-MY",
    # "tts": "ms-MY-YasminNeural",

}

# user_profile = {
#     "Name": "Jay Jay",
#     "Outstanding Debt Product": "Credit Card",
#     "Outstanding Debt Amount": "RM 5000",
#     "Date to make payment": "2024-04-30",
#     "Minimum Payment": "RM 100",
#     "Preferred Language": f"{languages['stt']}"
# }

# user_profile = {
#     "Name": "Ahmad",
#     "Outstanding Debt Product": "Credit Card",
#     "Outstanding Debt Amount": "RM 1273.45",
#     "Date to make payment": "2024-04-30",
#     "Minimum Payment": "RM 150",
#     "Preferred Language": f"{languages['stt']}"
# }

user_profile = {
    "Name": "陈小明",
    "Outstanding Debt Product": "Credit Card",
    "Outstanding Debt Amount": "RM 3201.20",
    "Date to make payment": "2024-04-30",
    "Minimum Payment": "RM 88",
    "Preferred Language": f"{languages['stt']}"
}


# from prompts.py
system_prompt = generate_response_to_human_system_prompt.format(
    Name=user_profile["Name"],
    Outstanding_Debt_Product=user_profile["Outstanding Debt Product"],
    Outstanding_Debt_Amount=user_profile["Outstanding Debt Amount"],
    Date_to_make_payment=user_profile["Date to make payment"],
    Days_left_to_make_payment=(datetime.strptime(user_profile["Date to make payment"], '%Y-%m-%d').date() - datetime.now().date()),
    Minimum_Payment=user_profile["Minimum Payment"],
    Preferred_Language=user_profile["Preferred Language"],
    Current_Date=datetime.now().strftime('%Y-%m-%d')
)



if languages["stt"] == "zh-CN":
    assistant_first_prompt=f"您好，我是RichRichMoney银行的人工智能语音助手。 我正在是和 {user_profile['Name']} 说话吗?"
elif languages["stt"] == "ms-MY":
    assistant_first_prompt=f"Hai, saya ialah pembantu suara yang dijana AI daripada bank RichRichMoney. Adakah saya bercakap dengan {user_profile['Name']} ?"
else:
    languages["stt"] == "en-SG"
    assistant_first_prompt=f"Hi, I am a AI generated voice assistant from a RichRichMoney bank. Am I speaking to {user_profile['Name']} ?"
    
memory = [
    {"role": "system", "content": system_prompt},
    {"role": "assistant" , "content": assistant_first_prompt},
    {"role": "assistant", "content": f"I prefer the conversation in {languages['stt']} language."}
]

def check_memory_and_yield_latest(call_id):
    call_id_memory = session_db.get(call_id)["memory"]
    memory_that_streamed = session_db.get(call_id)["memory_count_that_streamed"]

    if len(call_id_memory) > memory_that_streamed:
        memory_that_streamed = len(call_id_memory)
        yield call_id_memory

def generate_answer(prompt, history):
    if prompt == None: return   

    client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version = "2024-02-15-preview"
    
    )
    response = client.chat.completions.create(
        # model="gpt-35-turbo-16k",
        # model="gpt-35-turbo-0125",
        model="gpt4-0125",
        messages = history,
        temperature=0.05,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    answer = response.choices[0].message.content

    return answer



def generate_conversation_summary(call_id):

    conversation_memory = session_db.get(call_id)["memory"]
    summary_user_prompt = conversation_summary_user_prompt.format(
        json_dump_of_memory = json.dumps(conversation_memory[1:])
    )
                                                                  
    summary_system_prompt = conversation_summary_system_prompt.format(
                current_date=datetime.now().strftime('%Y-%m-%d, %A')
            )
    
    messages = [ {"role" : "system", "content": summary_system_prompt  },
                 {"role": "user", "content": summary_user_prompt}, 
                ]
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version = "2024-02-15-preview"
    )

    response = client.chat.completions.create(
        # model="gpt-35-turbo-16k",
        model="gpt-35-turbo-0125",
        # model="gpt4-0125",
        messages = messages,
        temperature=0,
        max_tokens=1000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    answer = response.choices[0].message.content
    return answer


def play_tts_and_recognize_reply_speech(call_connection_client: CallConnectionClient, text_to_play: str, target_participant:str, context: str):
    text_to_play = text_to_play
    play_source = TextSource(text=text_to_play, voice_name=languages["tts"]) 
    call_connection_client.start_recognizing_media(
        input_type=RecognizeInputType.SPEECH, 
        target_participant=target_participant, 
        end_silence_timeout=2.5, 
        play_prompt=play_source, 
        speech_language=languages["stt"],
        operation_context=context)
    

def play_tts(call_connection_client: CallConnectionClient, text_to_play: str, context: str):
        play_source = TextSource(text=text_to_play, voice_name=languages["tts"]) 
        call_connection_client.play_media_to_all(play_source, operation_context=context)


@app.route('/stream/<call_id>')
def stream(call_id):
    def event_stream():
        session_db.get(call_id)["memory_count_that_streamed"] = 0
        for item in check_memory_and_yield_latest(call_id):
            # yield f"data:{item}\n\n"
            yield f"data:{json.dumps(item)}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/resetmemory/<call_id>')
def reset_memory(call_id):
    session_db.get(call_id)["memory"] = memory.copy()
    session_db.get(call_id)["memory_count_that_streamed"] = 0

    return "Memory reset successfully"

@app.route('/summary/<call_id>')
def summary(call_id):

    return jsonify(generate_conversation_summary(call_id))


# GET endpoint to place phone call
@app.route('/outboundCall', methods=["POST"])
def outbound_call_handler():

    phone_number = request.form.get('mobilenumber')

    target_participant = PhoneNumberIdentifier(phone_number)
    source_caller = PhoneNumberIdentifier(ACS_PHONE_NUMBER)
    call_connection_properties = call_automation_client.create_call(target_participant, 
                                                                    CALLBACK_EVENTS_URI,
                                                                    cognitive_services_endpoint=COGNITIVE_SERVICES_ENDPOINT,
                                                                    source_caller_id_number=source_caller)
    app.logger.info("Created call with connection id: %s", call_connection_properties.call_connection_id)
    call_conn_id = call_connection_properties.call_connection_id
    session_db[call_conn_id] = { "phone_number": phone_number, "memory": memory.copy() , "memory_count_that_streamed": 0}
    return redirect(url_for('index_handler', call_id=call_conn_id, phone_number=phone_number))



# POST endpoint to handle callback events
@app.route('/api/callbacks', methods=['POST'])
def callback_events_handler():
    response_text = ""
    for event_dict in request.json:
        # Parsing callback events
        event = CloudEvent.from_dict(event_dict)
        call_connection_id = event.data['callConnectionId']
        app.logger.info("%s event received for call connection id: %s", event.type, call_connection_id)
        call_connection_client = call_automation_client.get_call_connection(call_connection_id)

        target_phone_number = session_db[call_connection_id]["phone_number"]
        target_participant = PhoneNumberIdentifier(target_phone_number)
        if event.type == "Microsoft.Communication.CallConnected":
            
            app.logger.info("Starting recognize")
            #call_connection_client.play_media_to_all(play_source)
            play_tts_and_recognize_reply_speech(call_connection_client, assistant_first_prompt , target_participant, "OpenQuestionSpeech")
            play_tts(call_connection_client=call_connection_client, text_to_play=TEXT_TO_PLAY_WHILE_WAITING, context="waiting")##Comment this line if not needed.
            
        # When speech recognizatino complete event
        elif event.type == "Microsoft.Communication.RecognizeCompleted":
            app.logger.info("Recognize completed: data=%s", event.data) 


            if event.data['recognitionType'] == "speech": 
                speech_text = event.data['speechResult']['speech']; 
                app.logger.info("Recognition completed, speech_text =%s", speech_text)


                session_memory = session_db.get(call_connection_id)["memory"]
                # start time
                session_memory.append( 
                    {"role": "user", "content": speech_text} 
                )
                start_time = datetime.now()
                response_text = generate_answer(speech_text, session_memory)
                end_time = datetime.now()
                session_memory.append({"role": "assistant", "content": response_text})
                session_db.get(call_connection_id)["memory"] = session_memory
                print (f"generated answer: {response_text}")
                print(f"Time taken GPT generate response: {end_time - start_time}")

                # if detect bye word, drop the call.
                if ('bye' in response_text.lower() or 
                  'selamat tinggal' in response_text.lower() or 
                  '再见' in response_text.lower() or 
                  '拜拜' in response_text.lower()
                  ):
                    play_tts(call_connection_client=call_connection_client, text_to_play=response_text, context="Ending")
                else:
                    play_tts_and_recognize_reply_speech(call_connection_client, response_text , target_participant, "OpenQuestionSpeech")
                    play_tts(call_connection_client=call_connection_client, text_to_play="AI is processing, please wait", context="waiting") ##Comment this line if not needed.


        elif event.type == "Microsoft.Communication.RecognizeFailed":
            failedContext = event.data['operationContext']
            if(failedContext and failedContext == "OpenQuestionSpeech"):
                play_tts_and_recognize_reply_speech(call_connection_client, INVALID_AUDIO , target_participant, RETRY_CONTEXT)
            elif (failedContext and failedContext == RETRY_CONTEXT):
                play_tts(call_connection_client=call_connection_client, text_to_play=NO_RESPONSE, context=RETRY_CONTEXT)
                call_connection_client.hang_up(is_for_everyone=True)
            else:
                call_connection_client.hang_up(is_for_everyone=True)


        elif event.type in ["Microsoft.Communication.PlayCompleted", "Microsoft.Communication.PlayFailed"]:
            prevContext = event.data['operationContext']
            if 'ending' in prevContext.lower():
                app.logger.info("Terminating call")
                call_connection_client.hang_up(is_for_everyone=True)           

        return Response(status=200, content_type="application/json", response=json.dumps({"text": response_text}))

# GET endpoint to render the menus
@app.route('/', defaults={'call_id': None, 'phone_number': None})
@app.route('/<call_id>/<phone_number>')
def index_handler(call_id, phone_number):
    return render_template("index.html", call_id=call_id, phone_number=phone_number)


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(port=8080, debug=True)
