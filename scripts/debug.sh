#!/bin/bash

# Skrypt do debugowania aplikacji FoodSave AI

set -e

echo "🔧 FoodSave AI - Debug Tools"
echo "=============================="

case "$1" in
    "dev")
        echo "🚀 Uruchamianie w trybie development (hot reload)..."
        docker-compose -f docker-compose.dev.yaml up --build -d
        echo "✅ Aplikacja uruchomiona w trybie development"
        echo "📝 Logi backend: docker-compose -f docker-compose.dev.yaml logs -f backend"
        echo "📝 Logi frontend: docker-compose -f docker-compose.dev.yaml logs -f frontend"
        ;;

    "prod")
        echo "🚀 Uruchamianie w trybie production..."
        docker-compose up --build -d
        echo "✅ Aplikacja uruchomiona w trybie production"
        ;;

    "logs")
        echo "📝 Wyświetlanie logów..."
        if [ "$2" = "backend" ]; then
            docker-compose logs -f backend
        elif [ "$2" = "frontend" ]; then
            docker-compose logs -f frontend
        elif [ "$2" = "ollama" ]; then
            docker-compose logs -f ollama
        else
            docker-compose logs -f
        fi
        ;;

    "shell")
        echo "🐚 Uruchamianie shell w kontenerze..."
        if [ "$2" = "backend" ]; then
            docker exec -it foodsave-backend bash
        elif [ "$2" = "frontend" ]; then
            docker exec -it foodsave-frontend sh
        else
            echo "Użycie: $0 shell [backend|frontend]"
        fi
        ;;

    "restart")
        echo "🔄 Restartowanie serwisu..."
        if [ "$2" = "backend" ]; then
            docker-compose restart backend
        elif [ "$2" = "frontend" ]; then
            docker-compose restart frontend
        else
            docker-compose restart
        fi
        echo "✅ Restart zakończony"
        ;;

    "clean")
        echo "🧹 Czyszczenie kontenerów i cache..."
        docker-compose down -v
        docker system prune -af
        echo "✅ Czyszczenie zakończone"
        ;;

    "status")
        echo "📊 Status kontenerów:"
        docker-compose ps
        echo ""
        echo "💾 Użycie dysku:"
        docker system df
        ;;

    "test")
        echo "🧪 Uruchamianie testów..."
        docker exec foodsave-backend python -m pytest tests/ -v
        ;;

    *)
        echo "Użycie: $0 {dev|prod|logs|shell|restart|clean|status|test}"
        echo ""
        echo "Komendy:"
        echo "  dev     - Uruchom w trybie development (hot reload)"
        echo "  prod    - Uruchom w trybie production"
        echo "  logs    - Pokaż logi (backend|frontend|ollama)"
        echo "  shell   - Wejdź do kontenera (backend|frontend)"
        echo "  restart - Restartuj serwis (backend|frontend)"
        echo "  clean   - Wyczyść kontenery i cache"
        echo "  status  - Pokaż status kontenerów"
        echo "  test    - Uruchom testy"
        echo ""
        echo "Przykłady:"
        echo "  $0 dev                    # Uruchom development"
        echo "  $0 logs backend           # Logi backendu"
        echo "  $0 shell backend          # Shell w backendzie"
        echo "  $0 restart backend        # Restart backendu"
        ;;
esac
