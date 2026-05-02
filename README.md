# 📩 Discord DM Dashboard Bot

Ce projet est un **dashboard web connecté à un bot Discord**, permettant de gérer et consulter les messages privés (DM) dans une interface moderne type messagerie (style Discord).

<img width="1917" height="961" alt="image" src="https://github.com/user-attachments/assets/e5aadefd-51a4-4856-8f61-5db42c31076e" />


## 🚀 Installation

Les messages privés envoyés au bot sont automatiquement interceptés grâce à l’événement Discord `on_message`.  
Ils sont ensuite transmis à l’API Flask pour être affichés en temps réel sur le dashboard.

```python
@bot.event
async def on_message(message):
               
    if message.author.bot:
        return
        
    if isinstance(message.channel, discord.DMChannel):

        attachments = []

        for a in message.attachments:
            attachments.append({
                "url": a.url
            })

        requests.post("http://IP_TO_FLASKSERVER:5000/message", json={
            "user_id": str(message.author.id),
            "content": message.content,
            "origin": "discord",
            "id": str(message.id),
            "attachments": attachments
        })

        return
```

Vous devez remplacer les sections marquées **"CHANGE ME"** par vos propres informations :

- 📁 Chemins locaux :
  - `DATA_FILE` → chemin du fichier JSON de stockage
  - `UPLOADS_PATH` → dossier des fichiers uploadés

- 🌐 URL serveur :
  - `URL_IMAGE` → URL publique de votre serveur d’images ou NAS

- 🤖 Bot Discord :
  - `DISCORD_BOT_TOKEN` → token de votre bot Discord
  - `DISCORD_GUILD_ID` → ID du serveur Discord ciblé
  - `HOST` → Changer l'ip avec celle la machine (Si besoin)
    
## 🚀 Fonctionnalités

- 💬 Gestion des DM Discord
  - Consultation des conversations privées des utilisateurs d’un serveur
  - Affichage de l’historique complet des messages
  - Envoi de messages directement depuis le dashboard

- 🧑‍💻 Interface web type Discord
  - Sidebar avec liste des conversations
  - Recherche de membres du serveur
  - Navigation fluide entre les chats

- 📸 Gestion des médias
  - Upload d’images depuis le dashboard
  - Affichage des images directement dans les messages
  - Support des fichiers envoyés

- 🔔 Système de notifications
  - Compteur de messages non lus
  - Mise à jour dynamique du titre de la page
  - Détection des nouveaux messages en temps réel

- 🗂️ Gestion des conversations
  - Suppression de conversations
  - Masquage de DM
  - Marquage comme lu

- 🤖 Intégration Discord API
  - Récupération des utilisateurs et avatars via bot Discord
  - Envoi automatique de messages privés
  - Gestion des channels DM via l’API officielle

- ⚡ Backend Flask
  - API REST pour messages, conversations et uploads
  - Stockage local en JSON
  - Système de cache pour optimiser les appels API

## 🛠️ Stack technique

- Python (Flask)
- Discord API (Bot)
- JavaScript vanilla (frontend)
- HTML / CSS (interface type Discord)
- JSON (stockage local)
- Requests (API HTTP)

## 📁 Fonctionnement

1. Le bot récupère les utilisateurs et messages Discord
2. Les données sont stockées localement en JSON
3. Le serveur Flask expose une API et une interface web
4. Le frontend interagit avec l’API en temps réel
5. Les messages envoyés depuis le dashboard sont transmis sur Discord

## 📌 Objectif

Créer une **interface centralisée de gestion des messages Discord**, permettant de consulter, répondre au nom du Bot et organiser les DM depuis un dashboard web personnalisé.

## 🔄 Évolution

Ce projet est en **constante évolution**.  
De nouvelles fonctionnalités et améliorations sont régulièrement ajoutées afin d’améliorer les performances, l’interface et l’expérience utilisateur.

## 🛠️ Support

Discord : https://discord.gg/dDUXt2J
Website : https://mraurontv.fr
