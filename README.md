# Orienta : chatbot d'orientation BBA et ABM

Orienta est un chatbot qui renseigne les futurs étudiants sur deux filières d'**IRGIB Africa University** : le **BBA** (Bachelor in Business Administration) et l'**ABM** (Analyses Biomédicales).

**Essayer en ligne : https://leonardobrayanne1-bit.github.io/orienta/**

Projet de groupe du cours d'Intelligence Artificielle, groupe G : DAVO Leonardo, AVALIGBE Ryan, GBONDJINON Ryan, ADELEYE Alimatou.

## Ce que fait le chatbot

- Il **accueille** l'utilisateur, y compris en langage courant (« yo », « cc », « c cmt ? »).
- Il répond sur les deux filières : présentation, matières, débouchés, admission, durée, stages, poursuite d'études.
- Il explique **29 notions** : NFS, prélèvement, hémolyse, bilan, marketing, SWOT, TVA…
- Il a une **mémoire** : « Et les stages ? » est compris comme une question sur la filière dont on vient de parler.
- Il **tolère les fautes de frappe** (« c koi les debouchers du bba »).
- Il **refuse poliment** les sujets hors de son domaine, ne donne jamais de diagnostic médical, et oriente vers le service des inscriptions pour les frais et les dates.
- C'est un chatbot **hybride** : il utilise l'IA Gemini quand il y a internet, et ses règles par mots-clés sans internet.

## Lancer le programme Python

1. Installer Python 3 (python.org).
2. Télécharger `bot.py`, l'ouvrir avec IDLE et appuyer sur **F5**.
3. Écrire une question après `Toi :`. Taper `aide` pour voir ce que sait le bot, `quitter` pour arrêter.

**Mode en ligne (facultatif)** : créer une clé API gratuite sur aistudio.google.com/apikey et la mettre dans un fichier `cle.txt` à côté de `bot.py`. Sans ce fichier, le bot fonctionne hors ligne. Ce fichier ne doit jamais être publié.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `bot.py` | Le chatbot en Python (règles + Gemini) |
| `index.html` | La version web de démonstration, avec le même cerveau par mots-clés |

## Comment il fonctionne

Message → nettoyage (minuscules, sans accents) → recherche des mots-clés exacts (filière, notion, sujet), puis avec tolérance aux fautes si rien n'est trouvé → mémoire de la conversation → réponse, demande de précision ou réponse par défaut.

## Utilisation de l'IA

Ce projet a été réalisé avec l'aide de Claude (Anthropic) pour le guidage, le code et la rédaction, et de Meta AI pour une partie des questions sur l'ABM. Les tests, les vérifications et les corrections ont été faits par le groupe.

Les informations sont générales : vérifiez-les auprès d'IRGIB Africa University.
