# Azure Speech & Azure OpenAI (include TTS) - Credit Card Debt Collection Sample with local microphone
## Speech To Text -> Azure OpenAI -> Text to Speech

In this quickstart, we cover how you can use Azure OpenAI & Azure Cognitive Search (Speech) together to make go thru a converastion with human. Go thru the notebook (.ipynb) for details.


## Prerequisites

- An Azure account with an active subscription. [Create an account for free](https://azure.microsoft.com/free/?WT.mc_id=A261C142F). 
- Create Azure AI Multi Service resource. For details, see [Create an Azure AI Multi service](https://learn.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account). or a Azure Speech service.
- - Azure OpenAI Service with 1 deployment (gpt35turbo or better chatcompletion model)
- [Python](https://www.python.org/downloads/) 3.8 or above.


### Setup the Python environment

Create and activate python virtual environment and install required packages using following command 
```
pip install -r requirements.txt
```

## Disclaimer

This repository is provided for proof of concept purposes only. The author is not responsible for any damage, loss, or other consequences that may occur as a result of using this repository for any purpose. Users are advised to use this repository at their own risk. The author makes no warranties, either expressed or implied, about the suitability, reliability, or accuracy of the information contained within this repository for any purpose.