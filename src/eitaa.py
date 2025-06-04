import requests

class Eitaa:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://eitaayar.ir/api/{self.token}/sendMessage"

    def send_message(self, chat_id, text, pin=False):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "pin": pin
        }
        try:
            response = requests.post(self.api_url, json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
