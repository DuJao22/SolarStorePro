import os
import google.generativeai as genai
from datetime import datetime
import time

class GeminiService:
    def __init__(self):
        self.api_keys = []
        
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        if google_api_key:
            self.api_keys.append(google_api_key)
        
        legacy_keys = [
            os.environ.get('GEMINI_API_KEY_1'),
            os.environ.get('GEMINI_API_KEY_2'),
            os.environ.get('GEMINI_API_KEY_3'),
            os.environ.get('GEMINI_API_KEY_4'),
            os.environ.get('GEMINI_API_KEY_5'),
        ]
        self.api_keys.extend([k for k in legacy_keys if k])
        self.current_key_index = 0
        self.failed_keys = set()
        self.last_rotation = datetime.now()
        self.model_name = 'gemini-2.0-flash'
        
        if self.api_keys:
            self._configure_current_key()
    
    def _configure_current_key(self):
        if self.api_keys:
            genai.configure(api_key=self.api_keys[self.current_key_index])
            print(f"[Gemini] Usando chave {self.current_key_index + 1} de {len(self.api_keys)}")
    
    def _rotate_key(self):
        if len(self.api_keys) <= 1:
            return False
        
        self.failed_keys.add(self.current_key_index)
        
        if len(self.failed_keys) >= len(self.api_keys):
            self.failed_keys.clear()
            print("[Gemini] Todas as chaves falharam, resetando...")
        
        for i in range(len(self.api_keys)):
            next_index = (self.current_key_index + 1 + i) % len(self.api_keys)
            if next_index not in self.failed_keys:
                self.current_key_index = next_index
                self._configure_current_key()
                self.last_rotation = datetime.now()
                print(f"[Gemini] Rotacionou para chave {self.current_key_index + 1}")
                return True
        
        return False
    
    def get_response(self, prompt, context=None, max_retries=5):
        if not self.api_keys:
            return "Desculpe, o assistente de IA não está configurado no momento."
        
        system_prompt = """Você é o assistente virtual da SolarPro, uma loja especializada em produtos de energia solar.
Seu papel é ajudar os clientes com:
- Informações sobre painéis solares, inversores e kits completos
- Orientação sobre qual produto é ideal para suas necessidades
- Explicações sobre economia de energia e retorno do investimento
- Dúvidas sobre instalação e garantia
- Informações sobre financiamento e formas de pagamento

Seja sempre cordial, profissional e objetivo. Use linguagem simples e acessível.
Se não souber a resposta, indique que o cliente pode entrar em contato pelo telefone ou WhatsApp."""

        if context:
            system_prompt += f"\n\nContexto adicional:\n{context}"
        
        full_prompt = f"{system_prompt}\n\nCliente: {prompt}\n\nAssistente:"
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    self.failed_keys.discard(self.current_key_index)
                    return response.text.strip()
                else:
                    return "Desculpe, não consegui processar sua pergunta. Tente novamente."
                    
            except Exception as e:
                error_msg = str(e).lower()
                print(f"[Gemini] Erro na tentativa {attempt + 1}/{max_retries} com chave {self.current_key_index + 1}: {e}")
                print(f"[Gemini] Tipo de erro: {type(e).__name__}")
                
                if 'quota' in error_msg or 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg:
                    print(f"[Gemini] Limite atingido, rotacionando chave...")
                    if self._rotate_key():
                        time.sleep(0.5)
                        continue
                    else:
                        return "O sistema está temporariamente sobrecarregado. Por favor, tente novamente em alguns minutos."
                
                elif 'invalid' in error_msg or 'api_key' in error_msg or '401' in error_msg or '403' in error_msg:
                    print(f"[Gemini] Chave inválida, rotacionando...")
                    if self._rotate_key():
                        continue
                    else:
                        return "Ocorreu um erro de configuração. Por favor, tente novamente mais tarde."
                
                else:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return f"Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."
        
        return "Desculpe, não foi possível obter uma resposta no momento. Tente novamente mais tarde."
    
    def get_product_recommendation(self, consumption_kwh, location=None, budget=None):
        prompt = f"Um cliente quer saber qual sistema solar é ideal para ele. Consumo mensal: {consumption_kwh} kWh."
        
        if location:
            prompt += f" Localização: {location}."
        if budget:
            prompt += f" Orçamento aproximado: R$ {budget}."
        
        prompt += " Recomende o melhor sistema e explique o retorno do investimento."
        
        return self.get_response(prompt)
    
    def get_savings_estimate(self, consumption_kwh, electricity_rate=0.75):
        prompt = f"""Calcule a economia para um cliente com:
- Consumo mensal: {consumption_kwh} kWh
- Tarifa de energia: R$ {electricity_rate}/kWh

Inclua:
1. Economia mensal estimada
2. Economia anual
3. Economia em 25 anos (vida útil do sistema)
4. Tempo estimado de retorno do investimento"""
        
        return self.get_response(prompt)
    
    def get_status(self):
        return {
            'total_keys': len(self.api_keys),
            'current_key': self.current_key_index + 1,
            'failed_keys': len(self.failed_keys),
            'last_rotation': self.last_rotation.isoformat() if self.last_rotation else None,
            'active': len(self.api_keys) > 0
        }

gemini_service = GeminiService()
