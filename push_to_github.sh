#!/bin/bash
# Push ARC-AGENTE02 to GitHub

set -e

cd ~/Projects/arc-agente02

echo "🚀 ARC-AGENTE02 GitHub Push Script"
echo "=================================="
echo

# Check if already has remote
if git remote | grep -q origin; then
    echo "✓ Remote origin ya configurado:"
    git remote -v
    echo
    read -p "¿Hacer push al remote existente? (s/n): " response
    if [ "$response" = "s" ]; then
        echo "Haciendo push..."
        git push -u origin main
        echo "✅ Push completado"
        exit 0
    fi
fi

# No remote configured - ask for username
echo "⚠️  No hay remote configurado"
echo
read -p "Usuario de GitHub: " github_user

if [ -z "$github_user" ]; then
    echo "❌ Usuario requerido"
    exit 1
fi

# Add remote
echo
echo "Configurando remote origin..."
git remote add origin https://github.com/$github_user/arc-agente02.git

# Ensure main branch
echo "Renombrando rama a main..."
git branch -M main

# Push
echo
echo "🔄 Haciendo push (49 commits)..."
git push -u origin main

echo
echo "✅ ¡Push completado exitosamente!"
echo
echo "Repositorio: https://github.com/$github_user/arc-agente02"
echo
echo "Próximos pasos:"
echo "1. Ir a tu repositorio en GitHub"
echo "2. Agregar descripción y topics"
echo "3. Configurar README si es necesario"
echo "4. Compartir enlace"
