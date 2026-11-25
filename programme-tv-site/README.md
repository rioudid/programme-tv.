# Programme TV du soir — site indépendant

Site statique pour Safari iPhone et iMac. Le site ouvre toujours sur le jour courant et conserve l'état de navigation lors des retours depuis les fiches externes.

## Ce qui est prêt
- Design adaptatif, sélecteur de date et de chaîne, première / deuxième partie de soirée
- Filtrage des émissions d'au moins 45 min commençant à partir de 20 h 45 (jusqu'à 2 h du matin)
- Collecte XMLTV France compressée, mise à jour programmée chaque jour à 7 h 17, heure de Paris
- Affichage du titre, horaires, durée, catégories, année et résumé quand la source les fournit
- Liens de recherche AlloCiné / Télé 7 Jours ; **pas de faux liens directs**
- Pas de dépendance Python externe, pas d'API payante, pas de ChatGPT quotidien

## Limites connues
- XMLTV France annonce jusqu'à 5 jours de grille. On ne peut pas garantir une semaine entière.
- Les numéros de chaîne peuvent varier sur Orange. Les chaînes 40 et 45 ne sont pas encore associées à une chaîne, à préciser.
- Les notes et liens directs AlloCiné / Télé 7 Jours ne sont pas collectés automatiquement : l'emplacement existe dans les fiches, mais il faut une source ou un enrichissement conforme.
- La diffusion / republication des données XMLTV doit respecter les conditions de la source. Vérifiez-les avant publication publique.
- GitHub peut parfois déclencher les mises à jour programmées en retard.

## Mettre en ligne via GitHub Pages
1. Créer un dépôt **public** nommé `programme-tv` dans votre compte GitHub.
2. Décompresser l'archive et importer **tout le contenu du dossier** à la racine du dépôt, y compris `.github/workflows/actualisation.yml`.
3. Dans `Settings` > `Pages` > `Build and deployment`, sélectionner `GitHub Actions`.
4. Dans `Actions`, sélectionner `Actualisation du programme TV`, puis `Run workflow` pour générer la première grille.
5. Une fois le déploiement fini, ouvrir `https://VOTRE_IDENTIFIANT.github.io/programme-tv/`.
6. Dans Safari iPhone, utiliser `Partager` > `Sur l'écran d'accueil`. Sur iMac, `Signets` > `Ajouter un signet`.

La page de départ reste la même ; seules les données sont actualisées chaque matin.

## Enrichir les films sans nouvelles recherches quotidiennes
Créer `cache/enrichissements.json` sous la forme :

```json
{
  "le jour le plus long": {
    "allocine_public": 4.1,
    "allocine_press": 3.7,
    "tele7_stars": 3,
    "allocine_url": "https://www.allocine.fr/film/fichefilm_gen_cfilm=XXXXX.html",
    "tele7_url": "https://www.programme-television.org/films/XXXXX"
  }
}
```

**Les URL ci-dessus sont des exemples de structure, pas des liens à utiliser.** Seuls les liens vérifiés doivent être saisis. Les enrichissements sont réutilisés d'une exécution à l'autre.

## Test local
`python -m http.server 8000 --directory site` puis ouvrir `http://localhost:8000/`. Pour lancer la collecte (nécessite internet) : `python build.py`.
