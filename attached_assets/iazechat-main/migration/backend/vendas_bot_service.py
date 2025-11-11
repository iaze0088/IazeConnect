"""
Serviço de Bot para Sistema de Vendas CyberTV
Gerencia apenas chamadas à API IPTV - IA controla tudo
"""
import re
import httpx
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class VendasBotService:
    """Bot service apenas para geração de testes"""
    
    def __init__(self):
        self.iptv_api_url = "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q"
    
    def extract_credentials(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai WhatsApp e PIN de texto livre
        Formatos aceitos:
        - "5511999999999 12"
        - "whatsapp: 5511999999999 senha: 12"
        """
        # Remover caracteres especiais
        clean_text = re.sub(r'[^\d\s]', ' ', text)
        numbers = clean_text.split()
        
        # Procurar número de telefone (10-13 dígitos) e PIN (2 dígitos)
        phone = None
        pin = None
        
        for num in numbers:
            if len(num) >= 10 and len(num) <= 13:
                phone = num
            elif len(num) == 2:
                pin = num
        
        return phone, pin
            bot_state
        )
    
    def extract_credentials(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai WhatsApp e PIN da mensagem
        Formato esperado: "5511999999999 25" ou "55 11 99999-9999 25"
        """
        # Remover caracteres especiais exceto espaços
        clean_message = re.sub(r'[^\d\s]', '', message)
        
        # Separar por espaços
        parts = clean_message.split()
        
        if len(parts) >= 2:
            # Juntar todos menos os últimos 2 dígitos (pode ser whatsapp fragmentado)
            whatsapp_parts = []
            pin = None
            
            for part in parts:
                if len(part) == 2 and part.isdigit() and pin is None:
                    pin = part
                else:
                    whatsapp_parts.append(part)
            
            whatsapp = ''.join(whatsapp_parts)
            
            # Se não encontrou PIN de 2 dígitos, pegar últimos 2 do último número
            if not pin and len(parts[-1]) >= 2:
                last_part = parts[-1]
                if len(last_part) == 2:
                    pin = last_part
                    whatsapp = ''.join(parts[:-1])
            
            return (whatsapp, pin)
        
        return (None, None)
    
    async def generate_test_and_respond(self, whatsapp: str, pin: str) -> Tuple[str, str]:
        """
        Chama API para gerar teste IPTV e retorna mensagem
        """
        try:
            logger.info(f"🔄 Gerando teste IPTV para WhatsApp: {whatsapp}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.iptv_api_url)
                
                if response.status_code == 200:
                    try:
                        # Tentar parsear como JSON primeiro
                        data = response.json()
                        logger.info(f"✅ API Response JSON: {data}")
                        
                        # Extrair usuário e senha do JSON
                        usuario = data.get('username') or data.get('usuario')
                        senha = data.get('password') or data.get('senha')
                        
                        if usuario and senha:
                            # Converter para string se necessário
                            usuario = str(usuario)
                            senha = str(senha)
                            
                            # Gerar mensagem de sucesso
                            message = (
                                "🎉 **Teste gerado com sucesso!**\n\n"
                                "📱 **Passo 1:** Baixe o aplicativo WA Suporte\n"
                                "👉 https://wppconnect-fix.preview.emergentagent.com\n\n"
                                "🔐 **Passo 2:** Faça login no WA Suporte\n"
                                f"WhatsApp: {whatsapp}\n"
                                f"Senha: {pin}\n\n"
                                "📺 **Passo 3:** Use estes dados no app de IPTV\n"
                                f"**Usuário:** {usuario}\n"
                                f"**Senha:** {senha}\n\n"
                                "⏰ **Validade:** 3 horas\n\n"
                                "Aproveite seu teste! Se tiver dúvidas, nosso suporte está disponível. 😊"
                            )
                            
                            return (message, "completed")
                    except:
                        # Se não for JSON, tentar extrair do texto
                        response_text = response.text
                        logger.info(f"✅ API Response Text: {response_text}")
                        
                        # Tentar extrair do texto
                        usuario_match = re.search(r'(Usuário|username):\s*(\d+)', response_text, re.IGNORECASE)
                        senha_match = re.search(r'(Senha|password):\s*(\w+)', response_text, re.IGNORECASE)
                        
                        if usuario_match and senha_match:
                            usuario = usuario_match.group(2)
                            senha = senha_match.group(2)
                            
                            message = (
                                "🎉 **Teste gerado com sucesso!**\n\n"
                                "📱 **Passo 1:** Baixe o aplicativo WA Suporte\n"
                                "👉 https://wppconnect-fix.preview.emergentagent.com\n\n"
                                "🔐 **Passo 2:** Faça login no WA Suporte\n"
                                f"WhatsApp: {whatsapp}\n"
                                f"Senha: {pin}\n\n"
                                "📺 **Passo 3:** Use estes dados no app de IPTV\n"
                                f"**Usuário:** {usuario}\n"
                                f"**Senha:** {senha}\n\n"
                                "⏰ **Validade:** 3 horas\n\n"
                                "Aproveite seu teste! Se tiver dúvidas, nosso suporte está disponível. 😊"
                            )
                            
                            return (message, "completed")
                    
                    logger.error(f"❌ Não foi possível extrair credenciais da resposta: {response.text}")
                else:
                    logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                
                # Fallback se API falhar
                return (
                    "❌ Desculpe, houve um erro ao gerar seu teste.\n\n"
                    "Por favor, aguarde um momento que um atendente irá te ajudar.",
                    "error"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao chamar API IPTV: {e}")
            return (
                "❌ Desculpe, houve um erro ao gerar seu teste.\n\n"
                "Por favor, aguarde um momento que um atendente irá te ajudar.",
                "error"
            )

# Instância global
vendas_bot = VendasBotService()
