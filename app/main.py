import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

origins = [
    "http://localhost:3000",
]

load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
openai = OpenAI()

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

history = {}

class MyAssiant:
  def __init__(self):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    self.openai = OpenAI()
    self.name = "Tri Pham"
    reader = PdfReader(os.path.join(current_dir, "me", "TRI-PHAM-TRAN-CV.pdf"))
    self.cv = ""
    for page in reader.pages:
      text = page.extract_text()
      if text:
        self.cv += text
    with open(os.path.join(current_dir, "me", "summary.txt"), "r", encoding="utf-8") as f:
      self.summary = f.read()
  def system_prompt(self):
        system_prompt = f"You are acting as {self.name}'s assistant. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and CV which you can use to answer questions. \
Be professional and engaging, as if talking to a {self.name}'s potential client or future employer who came across the website. \
If you don't know the answer to any question, Say you don't know and provide {self.name}'s email for user to contact directly. \
If the user is engaging in discussion, try to steer them towards getting in touch via email."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## CV:\n{self.cv}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}'s assistant."
        system_prompt += "Try to give answer in bullet points for readability"

        return system_prompt
  def chat(self, message, chatId):
    if chatId not in history:
        history[chatId] = []
    
    history[chatId].append({
        "content": message,
        "role": "user"
    })
    def generate():
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages= [{"role": "system", "content": self.system_prompt()}] + history[chatId] + [{"role": "user", "content": message}],
            stream=True
        )
        
        final_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                final_content += content
                yield content
        
        # Store the final content in history after streaming is complete
        history[chatId].append({
            "content": final_content,
            "role": "assistant"
        })

    return StreamingResponse(generate(), media_type="text/plain")

  


class MessageRequest(BaseModel):
    message: str
    chatId: str


myAssistant = MyAssiant()
@app.get("/")
async def root():
  return {"message": 'Hello World!'}

@app.post('/ask')
async def ask(request: MessageRequest):
    # if request.chatId not in history:
    #     history[request.chatId] = []
    
    # history[request.chatId].append({
    #     "content": request.message,
    #     "role": "user"
    # })

    # def generate():
    #     response = openai.chat.completions.create(
    #         model="gpt-4.1-mini",
    #         messages= history[request.chatId] + [{"role": "user", "content": request.message}],
    #         stream=True
    #     )
        
    #     final_content = ""
    #     for chunk in response:
    #         if chunk.choices[0].delta.content is not None:
    #             content = chunk.choices[0].delta.content
    #             final_content += content
    #             yield content
        
    #     # Store the final content in history after streaming is complete
    #     history[request.chatId].append({
    #         "content": final_content,
    #         "role": "assistant"
    #     })
    
    return myAssistant.chat(request.message, request.chatId)
    
  
  