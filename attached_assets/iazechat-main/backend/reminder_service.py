"""
Serviço de Envio de Lembretes de Vencimento
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ReminderService:
    """Serviço para enviar lembretes de vencimento"""
    
    def __init__(self):
        pass
    
    def send_email(self, smtp_config: Dict, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envia email usando SMTP
        
        Args:
            smtp_config: Configurações SMTP
            to_email: Email do destinatário
            subject: Assunto
            html_content: Conteúdo HTML
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
            msg['To'] = to_email
            
            # Adicionar conteúdo HTML
            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)
            
            # Conectar ao servidor SMTP
            with smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port']) as server:
                server.starttls()
                server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado para: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {to_email}: {e}")
            return False
    
    def generate_reminder_email(self, client_data: Dict, days_until: int) -> str:
        """
        Gera HTML do email de lembrete
        
        Args:
            client_data: Dados do cliente
            days_until: Dias até vencimento (negativo se já venceu)
            
        Returns:
            str: HTML do email
        """
        usuario = client_data.get('usuario', 'N/A')
        senha = client_data.get('senha', 'N/A')
        vencimento = client_data.get('vencimento', 'N/A')
        nome = client_data.get('nome', 'Cliente')
        
        if days_until > 0:
            status_msg = f"Sua assinatura vence em <strong>{days_until} dia(s)</strong>!"
            emoji = "⚠️"
            color = "#f59e0b"  # Amber
        elif days_until == 0:
            status_msg = "Sua assinatura vence <strong>HOJE</strong>!"
            emoji = "🚨"
            color = "#dc2626"  # Red
        else:
            status_msg = f"Sua assinatura venceu há <strong>{abs(days_until)} dia(s)</strong>!"
            emoji = "❌"
            color = "#991b1b"  # Dark red
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Lembrete de Vencimento</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f3f4f6;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: {color}; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px;">{emoji} Lembrete de Vencimento</h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="font-size: 18px; color: #374151; margin-bottom: 20px;">
                                        Olá, <strong>{nome}</strong>!
                                    </p>
                                    
                                    <div style="background-color: #fef3c7; border-left: 4px solid {color}; padding: 15px; margin-bottom: 25px;">
                                        <p style="margin: 0; font-size: 16px; color: #78350f;">
                                            {status_msg}
                                        </p>
                                    </div>
                                    
                                    <h3 style="color: #1f2937; margin-bottom: 15px;">📋 Seus Dados de Acesso:</h3>
                                    
                                    <table width="100%" cellpadding="10" style="background-color: #f9fafb; border-radius: 4px; margin-bottom: 25px;">
                                        <tr>
                                            <td style="font-weight: bold; color: #4b5563; width: 40%;">👤 Usuário:</td>
                                            <td style="color: #1f2937; font-family: monospace; font-size: 16px;">{usuario}</td>
                                        </tr>
                                        <tr>
                                            <td style="font-weight: bold; color: #4b5563;">🔐 Senha:</td>
                                            <td style="color: #1f2937; font-family: monospace; font-size: 16px;">{senha}</td>
                                        </tr>
                                        <tr>
                                            <td style="font-weight: bold; color: #4b5563;">📅 Vencimento:</td>
                                            <td style="color: #dc2626; font-weight: bold; font-size: 16px;">{vencimento}</td>
                                        </tr>
                                    </table>
                                    
                                    <div style="background-color: #dbeafe; border-radius: 4px; padding: 20px; margin-bottom: 25px;">
                                        <h4 style="color: #1e40af; margin-top: 0;">💡 Como Renovar:</h4>
                                        <ol style="color: #1e3a8a; margin: 0; padding-left: 20px;">
                                            <li style="margin-bottom: 8px;">Entre em contato com nosso suporte</li>
                                            <li style="margin-bottom: 8px;">Informe seu usuário para renovação</li>
                                            <li style="margin-bottom: 8px;">Realize o pagamento</li>
                                            <li>Aproveite seu serviço renovado!</li>
                                        </ol>
                                    </div>
                                    
                                    <div style="text-align: center; margin-top: 30px;">
                                        <a href="https://suporte.help" 
                                           style="background-color: #2563eb; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                                            📱 Falar com Suporte
                                        </a>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f3f4f6; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
                                    <p style="color: #6b7280; font-size: 14px; margin: 0;">
                                        Este é um email automático. Não responda a esta mensagem.
                                    </p>
                                    <p style="color: #9ca3af; font-size: 12px; margin-top: 10px;">
                                        © 2025 Sistema de Gestão. Todos os direitos reservados.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return html

# Instância global
reminder_service = ReminderService()
