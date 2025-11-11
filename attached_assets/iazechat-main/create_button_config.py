#!/usr/bin/env python3
"""
Script para criar configuração padrão de botões no /vendas
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid

async def create_button_config():
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'support_chat')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔌 Conectado ao MongoDB")
    
    # Criar configuração de botões
    button_config = {
        "mode": "button",  # Apenas botões, sem IA
        "welcome_message": "Olá! Como posso ajudar você hoje? Selecione uma opção:",
        "is_enabled": True,
        "root_buttons": [
            {
                "id": str(uuid.uuid4()),
                "label": "📞 SUPORTE",
                "response_text": "Você será atendido por nossa equipe de suporte em breve.",
                "action_type": "message",
                "is_active": True,
                "sub_buttons": []
            },
            {
                "id": str(uuid.uuid4()),
                "label": "🎁 TESTE GRÁTIS",
                "response_text": "Ótimo! Vamos configurar seu teste grátis.",
                "action_type": "message",
                "is_active": True,
                "sub_buttons": [
                    {
                        "id": str(uuid.uuid4()),
                        "label": "📱 Como funciona?",
                        "response_text": "Nosso teste grátis dura 3 horas e você tem acesso completo aos nossos canais de IPTV!",
                        "action_type": "message",
                        "is_active": True,
                        "sub_buttons": []
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "label": "✅ Quero o teste!",
                        "response_text": "Perfeito! Me informe seu WhatsApp e uma senha de 2 dígitos para gerar o teste.",
                        "action_type": "message",
                        "is_active": True,
                        "sub_buttons": []
                    }
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "label": "💰 PLANOS E PREÇOS",
                "response_text": "Nossos planos:\n\n1 mês - R$ 25,00\n3 meses - R$ 65,00\n6 meses - R$ 120,00\n12 meses - R$ 220,00",
                "action_type": "message",
                "is_active": True,
                "sub_buttons": []
            }
        ]
    }
    
    # Salvar no banco (garantir que o documento tenha id: "config")
    result = await db.config.update_one(
        {"id": "config"},
        {
            "$set": {
                "id": "config",
                "button_config": button_config
            }
        },
        upsert=True
    )
    
    if result.upserted_id:
        print(f"✅ Configuração de botões criada com sucesso!")
    elif result.modified_count > 0:
        print(f"✅ Configuração de botões atualizada com sucesso!")
    else:
        print(f"⚠️ Nenhuma alteração feita")
    
    # Verificar
    config = await db.config.find_one({"id": "config"}, {"button_config": 1})
    
    if config and "button_config" in config:
        button_cfg = config["button_config"]
        print(f"\n📊 Configuração salva:")
        print(f"   Modo: {button_cfg.get('mode')}")
        print(f"   Habilitado: {button_cfg.get('is_enabled')}")
        print(f"   Botões raiz: {len(button_cfg.get('root_buttons', []))}")
        
        for btn in button_cfg.get('root_buttons', []):
            print(f"   - {btn['label']} (Sub-botões: {len(btn.get('sub_buttons', []))})")
    else:
        print("❌ Configuração não encontrada no banco!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_button_config())
