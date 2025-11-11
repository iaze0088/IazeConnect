#!/bin/bash
# Script para atualizar credenciais no VPS 198.96.94.106

echo "🔧 Atualizando credenciais no MongoDB do VPS..."

# Conectar ao MongoDB e atualizar admin e atendentes
mongo support_chat << 'EOF'

// 1. Atualizar email do admin
db.users.updateOne(
  { user_type: "admin" },
  { 
    $set: { 
      email: "admin@admin.com",
      pass_hash: "$2b$12$aJlRikPuVr84.exj6v6hk.diQGJMwCezFZdpK1pu8fliiufpiexWq"
    }
  }
);
print("✅ Admin email atualizado para admin@admin.com");

// 2. Atualizar senha dos atendentes
const atendentes = ['biancaatt', 'leticiaatt', 'andressaatt', 'jessicaatt'];
const newHash = "$2b$12$qm8pZbfFDtnTtDRj6Vd9pO7OfrnBetQ8a2tnWX57ghgEvxtX8pkoS";

atendentes.forEach(username => {
  db.users.updateOne(
    { username: username, user_type: "agent" },
    { $set: { pass_hash: newHash } }
  );
  print("✅ Atendente " + username + " senha atualizada");
});

print("\n✅ TODAS AS CREDENCIAIS ATUALIZADAS COM SUCESSO!");

EOF

echo ""
echo "✅ Atualização concluída!"
echo ""
echo "📋 Credenciais atualizadas:"
echo "   Admin: admin@admin.com / 102030@ab"
echo "   Atendentes: biancaatt, leticiaatt, andressaatt, jessicaatt / ab181818ab"
