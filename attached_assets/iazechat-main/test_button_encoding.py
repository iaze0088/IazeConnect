#!/usr/bin/env python3
"""
Teste do encoding de button_config para bypass do gateway
"""
import requests
import json

BACKEND_URL = "https://suporte.help/api"

def test_vendas_start():
    """Testar endpoint /vendas/start"""
    print("🧪 TESTE: POST /vendas/start")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/vendas/start",
            json={"name": "Teste", "whatsapp": "5511999999999"},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n📦 Resposta completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Verificar empresa_nome
        if "empresa_nome" in data:
            print(f"\n✅ empresa_nome encontrado: {data['empresa_nome']}")
            
            # Tentar decodificar
            if data['empresa_nome'].startswith('BTNC:'):
                import base64
                try:
                    encoded = data['empresa_nome'].replace('BTNC:', '')
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    button_config = json.loads(decoded)
                    print(f"\n🔓 button_config DECODIFICADO:")
                    print(json.dumps(button_config, indent=2, ensure_ascii=False))
                    
                    if button_config.get('buttons'):
                        print(f"\n✅ {len(button_config['buttons'])} botões encontrados!")
                        for btn in button_config['buttons']:
                            print(f"  - {btn.get('label', 'N/A')}")
                    else:
                        print("\n⚠️ Nenhum botão encontrado no button_config")
                        
                except Exception as e:
                    print(f"\n❌ Erro ao decodificar: {e}")
            else:
                print(f"⚠️ empresa_nome não tem o prefixo BTNC:")
        else:
            print("\n❌ empresa_nome NÃO encontrado na resposta!")
            
        # Verificar se button_config direto existe (não deveria por causa do gateway)
        if "button_config" in data:
            print(f"\n⚠️ button_config DIRETO encontrado (gateway não bloqueou)")
            print(json.dumps(data['button_config'], indent=2, ensure_ascii=False))
        else:
            print(f"\n✅ button_config direto NÃO encontrado (esperado - gateway bloqueou)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE ENCODING DE BUTTON_CONFIG\n")
    test_vendas_start()
