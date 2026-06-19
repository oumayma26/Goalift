🤖 Integration IA — GoalCoach (Ollama)
Installation
1. Installer Ollama
Windows / macOS / Linux :
bash
# Telecharge depuis https://ollama.com/download
# Ou en ligne de commande :
curl -fsSL https://ollama.com/install.sh | sh
2. Telecharger un modele
bash
# Modele leger et rapide (recommande)
ollama pull llama3.2

# Alternative plus puissante
ollama pull qwen2.5:7b

# Ou modele tres leger pour vieux PC
ollama pull phi3:mini
3. Verifier que ca marche
bash
ollama run llama3.2
# Puis tape "exit" pour quitter
Ollama tourne maintenant en arriere-plan sur http://localhost:11434.
Fonctionnalites IA
🤖 Onglet Coach IA
Chat en temps reel avec un coach productivite
Suggestions rapides (definir un SMART goal, motivation, routine...)
Streaming : la reponse s'affiche mot par mot
100% offline — aucune donnee ne quitte ton PC
✨ Generation SMART dans GoalDialog
Decris ton objectif en langage naturel
L'IA genere :
Un titre SMART
Une description
Une deadline
Une couleur et priorite
Une liste de taches
Les taches sont creees automatiquement avec l'objectif
Architecture
plain
services/ai_coach.py       # Service de communication Ollama
ui/ai_coach_view.py        # Vue chat du coach IA
ui/dialogs.py              # GoalDialog avec section IA
Personnaliser le modele
Dans services/ai_coach.py :
Python
DEFAULT_MODEL = "llama3.2"  # Change ici
Modeles recommandes :
Table
Modele	Taille	Qualite	Vitesse
llama3.2	3B	⭐⭐⭐	⚡⚡⚡
qwen2.5:7b	7B	⭐⭐⭐⭐⭐	⚡⚡
phi3:mini	3.8B	⭐⭐⭐⭐	⚡⚡⚡
mistral:7b	7B	⭐⭐⭐⭐⭐	⚡⚡
Depannage
"Ollama n'est pas demarre"
bash
ollama serve  # Lance le serveur
"Aucun modele trouve"
bash
ollama list   # Liste les modeles disponibles
ollama pull llama3.2  # En telecharge un
Reponses trop lentes
Utilise un modele plus petit (llama3.2 au lieu de qwen2.5:7b)
Ou utilise un GPU : ollama run llama3.2 --gpu
Stack technique
Ollama : serveur LLM local
HTTP API : communication via requests (pas de SDK necessaire)
Threading : generation non-bloquante
Streaming : affichage temps reel token par token