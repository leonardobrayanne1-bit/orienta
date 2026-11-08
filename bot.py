# ===== Orienta : chatbot des filières BBA et ABM =====
# Bot hybride : Gemini (en ligne) + mots-clés (hors ligne)

import json
import os
import re
import unicodedata
import urllib.request


# ---- 0. Outils pour comprendre le texte ----
def nettoyer(texte):
    # Met en minuscules et enlève les accents : "Débouchés" -> "debouches"
    texte = texte.lower().strip()
    texte = unicodedata.normalize("NFD", texte)
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")


def distance(a, b):
    # Nombre de lettres à changer, ajouter ou enlever pour passer de a à b (distance de Levenshtein)
    precedente = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        ligne = [i]
        for j in range(1, len(b) + 1):
            cout = 0 if a[i - 1] == b[j - 1] else 1
            ligne.append(min(precedente[j] + 1, ligne[j - 1] + 1, precedente[j - 1] + cout))
        precedente = ligne
    return precedente[-1]


def contient(message, mot, flou=False):
    # Vrai si le mot-clé est dans le message.
    # - Expression de plusieurs mots ("formule sanguine") : on cherche le morceau de phrase.
    # - Mot seul ("bac") : il doit être un vrai mot du message (pluriel accepté),
    #   pour que "bac" ne soit pas trouvé dans "bachelor".
    # - flou=True (fautes de frappe) : pour un mot long, on accepte 1 erreur (2 si 8 lettres ou plus).
    if " " in mot or "'" in mot:
        return mot in message
    mots_du_message = re.findall(r"[a-z0-9]+", message)
    if mot in mots_du_message or mot + "s" in mots_du_message or mot + "x" in mots_du_message:
        return True
    if flou and len(mot) >= 6:
        tolerance = 2 if len(mot) >= 8 else 1
        for m in mots_du_message:
            if abs(len(m) - len(mot)) <= tolerance and distance(m, mot) <= tolerance:
                return True
    return False


# ---- 1. Reconnaître la filière ----
filieres = {
    "bba": ["bba", "business administration", "administration des affaires"],
    "abm": ["abm", "biomedical", "biomedicale", "biomedicales", "biomedicaux"],
}

# ---- 2. Les grands sujets (communs aux deux filières) ----
sujets = {
    "debouches": ["debouche", "metier", "travail", "emploi", "travailler", "boulot"],
    "matieres": ["matiere", "programme", "cours", "etudie", "apprend", "module"],
    "admission": ["admission", "condition", "serie", "bac", "inscrire", "inscription", "admis",
                  "g1", "g2", "g3", "f7", "f8", "peux faire", "peut faire", "accepte"],
    "duree": ["duree", "combien d'annees", "combien de temps", "combien d'ans", "dure"],
    "stages": ["stage"],
    "poursuite": ["master", "poursuite", "continuer", "doctorat", "apres la licence"],
}

reponses = {
    ("bba", "presentation"): "Le BBA (Bachelor in Business Administration) est une formation de 3 ans en gestion et management des entreprises : comptabilité, marketing, finance, ressources humaines, droit et stratégie.",
    ("bba", "debouches"): "Après le BBA, tu peux devenir assistant de gestion, chargé de clientèle en banque ou en microfinance, comptable, commercial, chargé de marketing, assistant RH, agent logistique ou créer ton entreprise.",
    ("bba", "matieres"): "En BBA, tu étudies la comptabilité, le marketing, la finance, la gestion des ressources humaines, le droit des affaires (OHADA), la fiscalité, l'économie, les statistiques, l'entrepreneuriat et l'anglais des affaires.",
    ("bba", "admission"): "Le BBA est ouvert à toutes les séries de BAC (G1, G2, G3, B, A, C, D...). L'admission se fait sur étude de dossier, parfois avec un test ou un entretien.",
    ("bba", "duree"): "Le BBA dure 3 ans, soit 6 semestres (180 crédits dans le système LMD).",
    ("bba", "stages"): "Oui ! En BBA, tu fais des stages en entreprise, et un stage de fin de cycle en 3e année avec un rapport ou un mémoire.",
    ("bba", "poursuite"): "Après le BBA, tu peux faire un Master : MBA, finance, marketing, ressources humaines, audit et contrôle de gestion ou logistique.",
    ("abm", "presentation"): "L'ABM (Analyses Biomédicales) est une formation de 3 ans qui forme des techniciens de laboratoire médical. L'analyse biomédicale, c'est l'étude du sang, des urines, des selles... pour aider le médecin à poser un diagnostic (NFS, glycémie, test de Widal...).",
    ("abm", "debouches"): "Après l'ABM, tu peux être technicien de laboratoire en hôpital ou en clinique, travailler dans un laboratoire privé ou de recherche, une banque de sang, être délégué médical ou faire du contrôle qualité en agroalimentaire.",
    ("abm", "matieres"): "En ABM, les matières principales sont l'hématologie, la biochimie, la microbiologie (bactériologie, parasitologie), l'immunologie, ainsi que l'hygiène et la sécurité au laboratoire.",
    ("abm", "admission"): "Pour l'ABM, il faut en général un BAC scientifique : série D ou C. L'admission se fait sur étude de dossier, parfois avec un test ou un entretien.",
    ("abm", "duree"): "L'ABM dure 3 ans et donne une Licence professionnelle (180 crédits LMD).",
    ("abm", "stages"): "Oui ! En ABM, tu fais des stages en laboratoire hospitalier, et un stage de fin de formation avec un mémoire.",
    ("abm", "poursuite"): "Après l'ABM, tu peux faire un Master en biologie médicale, biochimie, microbiologie ou santé publique, puis un doctorat.",
}

# ---- 3. Questions précises (FAQ) ----
# Chaque entrée : la filière, les mots-clés qui la reconnaissent, la réponse.
faq = [
    # ===== ABM =====
    {"filiere": "abm", "mots": ["nfs", "numeration", "formule sanguine", "hemogramme"],
     "reponse": "NFS = Numération Formule Sanguine. On compte les globules rouges, les globules blancs et les plaquettes. Elle peut montrer une anémie ou une infection."},
    {"filiere": "abm", "mots": ["a jeun", "jeun"],
     "reponse": "On demande d'être à jeun pour ne pas fausser le résultat : après un repas, le sucre et les graisses passent dans le sang, et la glycémie ou le cholestérol montent faussement."},
    {"filiere": "abm", "mots": ["serum", "plasma"],
     "reponse": "Le plasma, c'est le sang prélevé avec un anticoagulant. Le sérum, c'est le liquide obtenu quand le sang a coagulé, sans anticoagulant. Au labo, on utilise l'un ou l'autre selon l'analyse."},
    {"filiere": "abm", "mots": ["hygiene", "securite", "dasri", "gants", "blouse"],
     "reponse": "Au labo, on porte des gants et une blouse, on se lave les mains, on désinfecte la paillasse et on trie les déchets (DASRI) : les aiguilles vont dans des boîtes jaunes spéciales."},
    {"filiere": "abm", "mots": ["prelevement", "prelever", "prise de sang", "garrot"],
     "reponse": "Les étapes d'un prélèvement : 1) accueil et vérification de l'identité du patient, 2) pose du garrot, 3) désinfection, 4) prélèvement avec le tube adapté, 5) étiquetage immédiat du tube."},
    {"filiere": "abm", "mots": ["tube", "edta", "tube sec", "bouchon", "citrate"],
     "reponse": "Chaque tube a son rôle : le tube EDTA (bouchon violet) sert pour la NFS et le groupage ; le tube sec (bouchon rouge) pour la sérologie et la biochimie ; le tube citraté (bouchon bleu) pour la coagulation ; le tube fluoré (bouchon gris) pour la glycémie."},
    {"filiere": "abm", "mots": ["controle qualite", "qualite", "temoin"],
     "reponse": "Le contrôle qualité, c'est vérifier chaque jour que les automates donnent le bon résultat, avec des échantillons témoins. Si le témoin est faux, on ne rend pas les résultats des patients."},
    {"filiere": "abm", "mots": ["hemolyse"],
     "reponse": "L'hémolyse, c'est quand les globules rouges éclatent : le sérum devient rouge. Ça fausse beaucoup de résultats (le potassium par exemple), il faut alors refaire le prélèvement."},
    {"filiere": "abm", "mots": ["groupage", "groupe sanguin", "rhesus", "transfusion"],
     "reponse": "Le groupage sanguin sert à connaître le groupe A, B, AB ou O et le Rhésus (+ ou -). Il est indispensable avant une transfusion pour éviter un accident."},
    {"filiere": "abm", "mots": ["glycemie", "diabete", "sucre"],
     "reponse": "La glycémie, c'est le taux de sucre dans le sang. Au labo, on la mesure de préférence à jeun, sur un tube fluoré (bouchon gris)."},
    {"filiere": "abm", "mots": ["paludisme", "goutte epaisse", "frottis", "palu"],
     "reponse": "Pour le paludisme, le technicien fait une goutte épaisse et un frottis sanguin, puis cherche les parasites au microscope. On utilise aussi des tests de diagnostic rapide (TDR)."},
    {"filiere": "abm", "mots": ["microscope", "automate", "centrifugeuse", "materiel"],
     "reponse": "Au labo d'ABM, tu apprends à utiliser le microscope, la centrifugeuse, le spectrophotomètre et les automates d'analyse."},
    {"filiere": "abm", "mots": ["mon resultat", "mes resultats", "resultat anormal", "interpreter", "mon analyse", "mes analyses", "suis malade"],
     "reponse": "Je ne donne pas de diagnostic. Si un résultat est anormal, il faut voir ton médecin traitant avec le résultat : seul lui peut l'interpréter."},

    # ===== BBA =====
    {"filiere": "bba", "mots": ["comptabilite", "comptable", "compta"],
     "reponse": "La comptabilité, c'est enregistrer toutes les opérations de l'entreprise (achats, ventes, salaires...) pour connaître sa situation. En BBA, tu fais la comptabilité générale, puis la comptabilité analytique (le calcul des coûts)."},
    {"filiere": "bba", "mots": ["bilan"],
     "reponse": "Le bilan, c'est la photo du patrimoine de l'entreprise à une date : à gauche l'actif (ce qu'elle possède), à droite le passif (comment elle est financée : capitaux propres et dettes)."},
    {"filiere": "bba", "mots": ["compte de resultat", "benefice", "perte", "chiffre d'affaires"],
     "reponse": "Le compte de résultat montre l'activité de l'année : les produits (ventes) moins les charges (achats, salaires...). Si le résultat est positif, c'est un bénéfice ; sinon, une perte."},
    {"filiere": "bba", "mots": ["marketing", "4p", "mix", "publicite"],
     "reponse": "Le marketing, c'est comprendre les clients pour leur proposer la bonne offre. On utilise les 4P : Produit, Prix, Place (distribution) et Promotion (communication)."},
    {"filiere": "bba", "mots": ["grh", "ressources humaines", "recrutement", "rh"],
     "reponse": "La GRH (Gestion des Ressources Humaines), c'est gérer le personnel : recrutement, formation, salaires, évaluation, motivation et respect du droit du travail."},
    {"filiere": "bba", "mots": ["business plan", "plan d'affaires"],
     "reponse": "Le business plan, c'est le document qui présente un projet d'entreprise : l'idée, le marché, la stratégie, l'équipe et les prévisions financières. Il sert à convaincre une banque ou des investisseurs."},
    {"filiere": "bba", "mots": ["swot", "ffom"],
     "reponse": "L'analyse SWOT fait le point sur une entreprise : ses forces (Strengths) et faiblesses (Weaknesses) en interne, ses opportunités et menaces (Threats) dans son environnement."},
    {"filiere": "bba", "mots": ["ohada", "droit des affaires", "droit du travail", "societe", "sarl"],
     "reponse": "En BBA, tu étudies le droit des affaires OHADA : les règles communes à 17 pays africains pour créer et gérer une entreprise (SARL, SA...), les contrats et le droit du travail."},
    {"filiere": "bba", "mots": ["tva", "impot", "fiscalite", "taxe"],
     "reponse": "La fiscalité, ce sont les impôts de l'entreprise. Par exemple, la TVA (Taxe sur la Valeur Ajoutée) est ajoutée au prix de vente : l'entreprise la collecte auprès des clients et la reverse à l'État."},
    {"filiere": "bba", "mots": ["controle de gestion", "budget", "tableau de bord"],
     "reponse": "Le contrôle de gestion aide la direction à piloter l'entreprise : on fixe des budgets, on compare les prévisions aux résultats réels et on suit des tableaux de bord."},
    {"filiere": "bba", "mots": ["entrepreneuriat", "entrepreneur", "creer une entreprise", "creer mon entreprise", "creer son entreprise"],
     "reponse": "En BBA, le cours d'entrepreneuriat t'apprend à trouver une idée, étudier ton marché, faire un business plan et créer ton entreprise. Beaucoup de diplômés lancent leur propre activité."},
    {"filiere": "bba", "mots": ["finance", "tresorerie", "investissement", "rentabilite"],
     "reponse": "La finance d'entreprise étudie l'argent de l'entreprise : comment financer ses projets, gérer sa trésorerie, mesurer la rentabilité d'un investissement et analyser sa santé financière."},
    {"filiere": "bba", "mots": ["management", "manager", "leadership", "diriger"],
     "reponse": "Le management, c'est organiser et diriger une équipe pour atteindre les objectifs : planifier, motiver, communiquer et prendre des décisions."},
    {"filiere": "bba", "mots": ["anglais", "english"],
     "reponse": "En BBA, l'anglais des affaires (Business English) est renforcé : réunions, e-mails professionnels, présentations. C'est un vrai plus pour travailler dans les entreprises internationales."},
    {"filiere": "bba", "mots": ["data", "analyst", "analyste", "analytics", "donnees", "business analyst", "data analyst"],
     "reponse": "Oui ! Après le BBA, tu peux viser un Master en business analytics ou en data analysis. Les statistiques, la finance et la gestion du BBA sont une bonne base ; il faudra renforcer les maths et l'informatique (Excel avancé, SQL, Python, Power BI)."},
    {"filiere": "bba", "mots": ["commerce international", "import", "export", "logistique", "transit"],
     "reponse": "En BBA, tu découvres le commerce international et la logistique : importer, exporter, le transit, les douanes et la gestion des stocks."},
]

# ---- 4. Le cerveau HORS LIGNE (mots-clés) ----
derniere_filiere = None   # le bot se souvient de la dernière filière dont on a parlé
sujet_en_attente = None   # le sujet de la question quand le bot a demandé "BBA ou ABM ?"


def trouver_filiere(message, flou=False):
    trouvees = []
    for nom, mots in filieres.items():
        for mot in mots:
            if contient(message, mot, flou) and nom not in trouvees:
                trouvees.append(nom)
    return trouvees


def trouver_faq(message, flou=False):
    # On donne un score à chaque question : le nombre de mots-clés trouvés.
    meilleure = None
    meilleur_score = 0
    for entree in faq:
        score = 0
        for mot in entree["mots"]:
            if contient(message, mot, flou):
                score = score + 1
        if score > meilleur_score:
            meilleur_score = score
            meilleure = entree
    return meilleure


def trouver_sujet(message, flou=False):
    sujet = "presentation"
    for nom, mots in sujets.items():
        for mot in mots:
            if contient(message, mot, flou):
                sujet = nom
    return sujet


def cerveau_hors_ligne(question):
    global derniere_filiere, sujet_en_attente
    message = nettoyer(question)

    # a) Politesse
    if any(contient(message, m) for m in ["merci", "thanks"]):
        return "Avec plaisir ! As-tu d'autres questions sur BBA ou ABM ?"
    if any(contient(message, m) for m in ["frais", "prix", "cout", "coute", "scolarite", "payer", "rentree",
                                          "contact", "telephone", "adresse", "numero", "date"]):
        return ("Je n'ai pas les informations pratiques de l'école (frais, dates, contacts). "
                "Pour ça, adresse-toi au service des inscriptions d'IRGIB Africa University : une personne pourra te répondre.")
    if any(contient(message, m) for m in ["aide", "help", "que sais tu faire", "tu fais quoi"]):
        return ("Je peux te parler des filières BBA et ABM : présentation, matières, débouchés, admission, durée, stages, "
                "études après la licence. Je peux aussi t'expliquer des notions comme la NFS, le bilan, le marketing...")

    # b) On cherche d'abord les mots-clés EXACTS : filière, question précise (FAQ), grand sujet
    filieres_trouvees = trouver_filiere(message)
    entree = trouver_faq(message)
    sujet = trouver_sujet(message)

    # c) Rien trouvé ? On réessaie en tolérant les fautes de frappe
    if not filieres_trouvees and entree is None and sujet == "presentation":
        filieres_trouvees = trouver_filiere(message, flou=True)
        entree = trouver_faq(message, flou=True)
        sujet = trouver_sujet(message, flou=True)
    elif entree is None and sujet == "presentation":
        sujet = trouver_sujet(message, flou=True)

    if entree is not None:
        derniere_filiere = entree["filiere"]
        sujet_en_attente = None
        return entree["reponse"]

    # Réponse à "BBA ou ABM ?" : on reprend le sujet de la question précédente
    if sujet == "presentation" and sujet_en_attente is not None and len(filieres_trouvees) == 1:
        sujet = sujet_en_attente
    sujet_en_attente = None

    # d) On choisit la réponse
    if len(filieres_trouvees) == 2:
        derniere_filiere = None                   # on a parlé des deux : plus de filière "en cours"
        return reponses[("bba", sujet)] + "\n" + reponses[("abm", sujet)]
    if len(filieres_trouvees) == 1:
        derniere_filiere = filieres_trouvees[0]
        return reponses[(derniere_filiere, sujet)]
    if sujet != "presentation":
        if derniere_filiere is not None:          # "et les stages ?" -> on reprend la filière précédente
            return reponses[(derniere_filiere, sujet)]
        sujet_en_attente = sujet                  # on retient le sujet en attendant la filière
        return "Tu parles de BBA ou de ABM ?"
    if any(contient(message, m) for m in ["ca va", "cava", "cmt", "comment vas tu", "comment tu vas",
                                          "tu vas bien", "la forme", "quoi de neuf"]):
        return "Ça va bien, merci ! Et toi ? Je suis là pour répondre à tes questions sur BBA et ABM."
    if any(contient(message, m) for m in ["bonsoir", "bsr", "bonne soiree"]):
        return "Bonsoir ! Que veux-tu savoir sur BBA ou ABM ?"
    if any(contient(message, m) for m in ["bonjour", "bonsoir", "salut", "slt", "bjr", "bsr", "cc", "coucou",
                                          "yo", "hello", "hi", "hey", "wesh", "bonne journee", "bonne soiree"]):
        return "Bonjour ! Que veux-tu savoir sur BBA ou ABM ?"
    return ("Désolé, je ne peux pas t'aider sur ce sujet. Je parle uniquement des filières BBA et ABM. "
            "Tu peux me demander par exemple : les matières, les débouchés ou les conditions d'admission.")


# ---- 5. Le cerveau EN LIGNE (Gemini) ----
try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:          # certains sites Python en ligne ne connaissent pas __file__
    DOSSIER = os.getcwd()
MODELE = "gemini-flash-lite-latest"


def lire_cle():
    # Lit la clé API dans le fichier cle.txt (à côté de bot.py)
    try:
        with open(os.path.join(DOSSIER, "cle.txt"), encoding="utf-8-sig") as f:
            return f.read().strip()
    except OSError:        # fichier absent ou illisible -> pas de mode en ligne
        return None


def internet_disponible():
    # Essaie de joindre Google en 10 secondes maximum
    try:
        urllib.request.urlopen("https://www.google.com", timeout=10)
        return True
    except Exception:
        return False


# Les règles du bot + tout ce qu'il sait (envoyé à Gemini)
connaissances = "\n".join(f"- {f.upper()} / {s} : {r}" for (f, s), r in reponses.items())
connaissances += "\n" + "\n".join(f"- {e['filiere'].upper()} : {e['reponse']}" for e in faq)
REGLES = f"""Tu es Orienta, l'assistant des filières BBA (Bachelor in Business Administration)
et ABM (Analyses Biomédicales). Tu réponds en français, de façon chaleureuse et courte (3 phrases maximum).
Tu accueilles poliment les personnes qui te saluent. Elles écrivent souvent en abrégé :
"cc", "slt", "yo", "bjr", "bsr" veulent dire bonjour ; "c cmt ?" ou "cmt" veulent dire "comment ça va ?".
Réponds-y naturellement, puis propose ton aide sur BBA et ABM.
Tu parles UNIQUEMENT de BBA et ABM : la formation, ses matières et les notions enseignées
(comptabilité, marketing, NFS, prélèvement...), les débouchés, l'admission, la durée, les stages,
les études après, et l'aide au choix entre les deux filières.
Pour toute autre demande, tu refuses poliment : "Désolé, je ne peux pas t'aider sur ce sujet. Je parle uniquement des filières BBA et ABM."
Tu ne donnes jamais de diagnostic ni d'interprétation de résultats personnels : tu renvoies vers un médecin.
Tu n'inventes pas les frais, dates ou contacts de l'école : si tu ne sais pas, dis de contacter le service des inscriptions.
Voici tes connaissances :
{connaissances}"""

historique = []   # la conversation, pour que Gemini se souvienne des questions précédentes


def cerveau_en_ligne(question, cle):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELE}:generateContent"
    messages = historique[-8:] + [{"role": "user", "parts": [{"text": question}]}]
    donnees = {
        "system_instruction": {"parts": [{"text": REGLES}]},
        "contents": messages,
    }
    requete = urllib.request.Request(
        url,
        data=json.dumps(donnees).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": cle},
    )
    with urllib.request.urlopen(requete, timeout=90) as reponse:
        resultat = json.loads(reponse.read().decode("utf-8"))
    texte = resultat["candidates"][0]["content"]["parts"][0]["text"].strip()
    historique.append({"role": "user", "parts": [{"text": question}]})
    historique.append({"role": "model", "parts": [{"text": texte}]})
    return texte


# ---- 6. Accueil ----
print("Bonjour et Bienvenue ! Je suis Orienta.")
print("Je réponds à tes questions sur les filières BBA et ABM !")
print("Tape 'aide' pour savoir ce que je sais faire, ou 'quitter' pour arrêter.")

cle = lire_cle()
if cle and internet_disponible():
    print("(Mode EN LIGNE : Gemini est activé)")
else:
    print("(Mode HORS LIGNE : réponses par mots-clés)")
print()

# ---- 7. La discussion ----
while True:
    question = input("Toi : ")
    if nettoyer(question) in ["quitter", "exit", "au revoir", "bye"]:
        print("Orienta : Au revoir et bonne chance pour ton orientation !")
        break
    if question.strip() == "":
        continue

    # Clé présente -> on essaie Gemini. En cas d'erreur (pas d'internet...) -> hors ligne.
    if cle:
        try:
            print("Orienta :", cerveau_en_ligne(question, cle))
            continue
        except Exception as erreur:
            print("(Gemini indisponible :", erreur, "-> passage en mode hors ligne)")

    print("Orienta :", cerveau_hors_ligne(question))
