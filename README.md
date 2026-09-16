Résumé

Projet d'appli de chat multiplateforme (Win/Lin/Android) inspirée de Matrix/XMPP/Discord

Détails
veut créer une appli de chat compatible Windows, Linux et Android
s'inspire de Matrix, XMPP et Discord
veut un thème très personnalisable (couleurs etc., façon Nitro sur Discord)
veut une authentification simple nom d'utilisateur/mot de passe, sans 2FA
veut que l'app soit facile d'accès et open source
veut un panneau d'administration pour accéder au backend
a choisi de construire sur un protocole existant (Matrix/XMPP) plutôt qu'un backend custom
a un niveau de programmation "some experience" (intermédiaire)
veut pouvoir basculer facilement entre un serveur local et un serveur en ligne
Avancement
Serveur Synapse local fonctionnel (Docker, Ubuntu, sqlite3), compte admin "xivver" créé, connexion confirmée avec matrix-nio en Python
Cycle complet confirmé en Python/matrix-nio : création de salon, envoi de message, lecture de message (tout fonctionne)
Client Kivy/KivyMD en Python démarré : écran de connexion fonctionnel (asyncio intégré via async_run), connexion testée avec succès
Flux complet fonctionnel dans le client Kivy : connexion → liste des salons → écran de discussion (historique + envoi de message)
ordre de développement choisi : 1) système de thèmes personnalisables, 2) mises à jour en temps réel, 3) écran d'inscription, 4) packaging Android/Windows
Système de thèmes de base ajouté (JSON avec couleurs + polices, chargé via load_theme() et appliqué à theme_cls) ; app testée à nouveau avec succès (connexion, salons, messages)
veut aussi une page web accessible uniquement quand son PC est allumé (en plus du client Kivy)
Écran de thème (choix de couleur) et envoi de message avec la touche Entrée ajoutés et fonctionnels
Rafraîchissement en temps réel ajouté (sync_forever + callback sur nouveaux messages)
Progrès autonomes de l'utilisateur : écran d'inscription (register), écrans "nouveau chat" et "nouveau groupe", module user_store.py qui enregistre les comptes localement avec un statut is_superuser
veut un panneau d'admin avec un bouton pour promouvoir n'importe quel utilisateur en superutilisateur, et un écran de paramètres de compte avec option de quitter/désactiver le compte
le tableau de bord admin doit être intégré directement dans l'appli Kivy (pas une appli Flask séparée) ; les superutilisateurs sont redirigés vers ce tableau de bord au lieu de l'appli de chat normale
Tableau de bord admin intégré dans l'appli (AdminScreen) : inscription de nouveaux utilisateurs, liste des utilisateurs, bouton "Promote" fonctionnel (local + appel à l'Admin API de Synapse)
veut plus d'outils de modération : rétrograder/désactiver des comptes, réinitialiser un mot de passe, bannir/expulser d'un salon, supprimer un message (redaction), et plus encore
Outils de modération ajoutés dans AdminScreen : promote/demote (toggle), désactivation de compte, réinitialisation de mot de passe, kick/ban de salon, suppression de message (redaction)
veut maintenant prioriser : rendre l'appli accessible à d'autres personnes + compatibilité Windows (avant de continuer sur d'autres fonctionnalités)
Code complet fusionné en un seul main.py (thèmes, temps réel, inscription, nouveau chat/groupe, tableau de bord admin avec modération complète)
veut mettre en place en même temps : le tunnel Cloudflare (pour rendre le serveur accessible) et un dépôt Git (pour distribuer le code)
Tunnel Cloudflare configuré et fonctionnel (cloudflared installé, tunnel actif)
compte GitHub : xivver-tech
Dépôt Git créé et code poussé avec succès sur github.com/xivver-tech/chatapp
Test réussi avec 2 comptes distincts (ayoub, yahya/xivver) mais salons non synchronisés (invitations pas acceptées automatiquement) ; correctif ajouté : auto-acceptation des invitations de salon via callback SyncResponse
veut ensuite : vrais thèmes avancés (effets overlay façon Nitro Discord), messages façon WhatsApp (bulles), notifications, mentions (@) ; a choisi de commencer par les mentions (@)
Mentions (@) ajoutées : détection par regex, mise en forme en gras/bleu, surlignage du message si l'utilisateur connecté est mentionné
A créé un logo pour l'application (bulle de dialogue blanche avec 3 points colorés, fond dégradé violet-bleu, étincelle)
veut créer un APK Android pour l'application
Build Buildozer entièrement nettoyé (.buildozer supprimé) pour repartir à zéro
a choisi de développer ensuite : effets de thème avancés/overlay (façon Nitro Discord)
Effets overlay ajoutés (fond dégradé, halo de mention) mais le dégradé ne s'affichait pas (bug : jamais attaché au canvas) ; correctif appliqué + suppression du domaine "localhost" codé en dur (dérivé dynamiquement du serveur homeserver à la place)
veut que l'app soit entièrement en Python
veut une interface propre/correcte sur toutes les plateformes, sans viser un niveau ultra poli (pas besoin d'un niveau "Nitro")
