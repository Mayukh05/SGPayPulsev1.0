"""Provider registry and clients. No network activity during import."""
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class ModelOption:
    provider: str
    label: str
    model_id: str

class ModelError(RuntimeError):
    def __init__(self, category: str, message: str):
        self.category=category
        super().__init__(message)

def configured_models(settings: Mapping[str,str]) -> list[ModelOption]:
    result=[]
    if settings.get('OPENAI_API_KEY'):
        allowed=[x.strip() for x in settings.get('OPENAI_ALLOWED_MODELS','gpt-4.1-mini,gpt-4.1').split(',') if x.strip()]
        result += [ModelOption('OpenAI',x,x) for x in allowed]
    if settings.get('AZURE_OPENAI_API_KEY') and settings.get('AZURE_OPENAI_ENDPOINT') and settings.get('AZURE_OPENAI_DEPLOYMENTS'):
        result += [ModelOption('Azure OpenAI',x,x) for x in settings['AZURE_OPENAI_DEPLOYMENTS'].split(',') if x.strip()]
    return result

def classify_error(exc: Exception) -> ModelError:
    name=type(exc).__name__
    if name in ('AuthenticationError','PermissionDeniedError'):return ModelError('authentication','The model provider rejected the credentials or access permissions. Contact the application administrator.')
    if name=='RateLimitError':return ModelError('rate_limit','The selected model is rate-limited or has reached its quota. Try again later.')
    if name in ('APITimeoutError','APIConnectionError'):return ModelError('connection','The selected AI provider could not be reached. Check the approved network, proxy, certificate, or endpoint configuration.')
    if name in ('BadRequestError','NotFoundError'):return ModelError('model','The selected model or Azure deployment is unavailable or misconfigured. Contact the administrator.')
    return ModelError('provider','The AI provider could not complete the request. Please try again or contact the administrator.')

def generate(option: ModelOption, settings: Mapping[str,str], messages: list[dict]) -> str:
    try:
        from openai import OpenAI, AzureOpenAI
        if option.provider=='OpenAI':
            client=OpenAI(api_key=settings['OPENAI_API_KEY'],timeout=30,max_retries=1)
        elif option.provider=='Azure OpenAI':
            client=AzureOpenAI(api_key=settings['AZURE_OPENAI_API_KEY'],azure_endpoint=settings['AZURE_OPENAI_ENDPOINT'],api_version=settings.get('AZURE_OPENAI_API_VERSION','2024-10-21'),timeout=30,max_retries=1)
        else:raise ModelError('configuration','Unknown model provider.')
        response=client.chat.completions.create(model=option.model_id,messages=messages,temperature=0)
        content=response.choices[0].message.content
        if not content:raise ModelError('provider','The model returned an empty response.')
        return content
    except ModelError:raise
    except Exception as exc:raise classify_error(exc) from exc
