# Call Automation with Azure Speech & Azure OpenAI - Credit Card Debt Collection Sample
## Speech To Text -> Azure OpenAI -> Text to Speech

In this quickstart, we cover how you can use Call Automation SDK, Azure OpenAI & Azure Cognitive Search (Speech) together to make an outbound call to a phone number to play dynamic prompts to participants using Text-to-Speech and recognize user voice input through Speech-to-Text to drive business logic in your application. Modify the `app.py` files to switch to the 3 langugues that writing in the code which is "en-SG", "zh-CN", "ms-MY". Sample profile can be found in `app.py` too. (Example: Credit card balance, minimum payment etc.)


## Prerequisites

- An Azure account with an active subscription. [Create an account for free](https://azure.microsoft.com/free/?WT.mc_id=A261C142F). 
- A deployed Communication Services resource. [Create a Communication Services resource](https://docs.microsoft.com/azure/communication-services/quickstarts/create-communication-resource).
- A [phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number) in your Azure Communication Services resource that can make outbound calls. NB: phone numbers are not available in free subscriptions.
- Create Azure AI Multi Service resource. For details, see [Create an Azure AI Multi service](https://learn.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account).
- Azure OpenAI Service with 1 deployment (gpt35turbo or better chatcompletion model)
- Create and host a Azure Dev Tunnel. Instructions [here](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started) OR use Ngrok for Tunnelling. `ngrok http 8080` to start expose your local machine port to be accessible via an public URL. Ngrok will give you a public URL that map to your localhost:port
- [Python](https://www.python.org/downloads/) 3.8 or above.


### Setup the Python environment

Create and activate python virtual environment and install required packages using following command 
```
pip install -r requirements.txt
```

### Setup and host your Azure DevTunnel or use Ngrok

[Azure DevTunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/overview) is an Azure service that enables you to share local web services hosted on the internet. Use the commands below to connect your local development environment to the public internet. This creates a tunnel with a persistent endpoint URL and which allows anonymous access. We will then use this endpoint to notify your application of calling events from the ACS Call Automation service.

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host
```

OR 

[Ngrok](https://ngrok.com/docs/guides/getting-started/). Follow the guide to setup. You can skip this if you deploy to a public facing service (eg: Azure Web App, VM with public IP)
```bash
ngrok http 8080
```

The idea is to let Azure Communication Service to reach to your application from internet.

### Configuring application

Rename the file `.env.sample` to `.env` and configure the following settings

1. `AZURE_OPENAI_ENDPOINT`= Azure OpenAI Service Endpoint
2. `AZURE_OPENAI_API_KEY`= Azure OpenAI Service API Key
3. `ACS_CONNECTION_STRING`= Azure Communication Service resource's connection string. You can get via Azure Portal
4. `ACS_PHONE_NUMBER`= Phone number associated with the Azure Communication Service resource. For e.g. "+1425XXXAAAA"
5. `CALLBACK_URI_HOST`= Base url of the app. (For local development use dev tunnel url or ngrok eg in ngrok: https://xxxxyyyzzz.ngrok-free.app )
6. `CALLBACK_EVENTS_URI`= The path for the event callback to reach out. You can keep the value as "/api/callbacks" path . 
7. `COGNITIVE_SERVICES_ENDPOINT`= The multi service Azure Cognitive Service Endpoint
8. `TEMPLATE_FILES_PATH`="template" can keep it as template.


Check out `prompts.py` for Azure OpenAI Chat Completion prompt. Adjust accordingly to your use case. 

## Run app locally

1. Navigate to `/` folder and run `app.py` in debug mode.
2. Browser should pop up with the below page. If not navigate it to `http://localhost:8080/` or your dev tunnel url.
3. To initiate the call, key in a mobile number and click on the `Call Out` button.
4. Click `Start Stream` to see the conversation dialog.
5. Click `Get Summary` at the end of the call to get the call's summary.


## Disclaimer

This repository is provided for proof of concept purposes only. The author is not responsible for any damage, loss, or other consequences that may occur as a result of using this repository for any purpose. Users are advised to use this repository at their own risk. The author makes no warranties, either expressed or implied, about the suitability, reliability, or accuracy of the information contained within this repository for any purpose.