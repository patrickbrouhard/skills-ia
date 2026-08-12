# Résumer une vidéo YouTube

Produire en Markdown un résumé clair, fidèle et synthétique à partir de la
transcription. Ne pas commenter le processus ni ajouter d'information,
d'interprétation ou de recommandation absente de la vidéo.

La transcription peut contenir des erreurs ou des omissions. Utiliser le
contexte lorsque le sens est raisonnablement identifiable, mais ne jamais
présenter une reconstruction incertaine comme un fait.

## Principes

- Identifier le sujet, l'idée centrale et les conclusions principales.
- Conserver les arguments, exemples, chiffres et nuances qui contribuent
  réellement à la compréhension.
- Supprimer les répétitions, digressions, promotions et détails secondaires.
- Organiser les idées par thèmes, arguments ou étapes du raisonnement, pas
  minute par minute.
- Hiérarchiser : un contenu plus dense demande davantage de structure, pas une
  restitution proportionnellement plus longue.
- Ne pas répéter la même idée dans plusieurs sections.
- Ne reprendre une conclusion ou une recommandation que si la vidéo la soutient
  explicitement.

## Structure adaptative

Commencer par `## En bref` : deux ou trois phrases donnant immédiatement le
sujet, l'objectif ou l'idée principale, puis la conclusion lorsqu'il y en a
une.

Ajouter seulement les sections utiles parmi les suivantes :

- `## Points clés` pour une vue d'ensemble rapide ;
- des sections aux titres descriptifs pour développer les thèmes, arguments ou
  étapes importants ;
- `## Faits, chiffres ou exemples importants` si certains éléments concrets
  doivent être retrouvés facilement ;
- `## Nuances, objections ou limites` lorsque ces réserves sont présentes dans
  la vidéo et nécessaires à une compréhension fidèle ;
- `## Ressources mentionnées` pour les ressources explicitement citées et
  suffisamment identifiables, sans recherche ni ajout extérieur.

Ces sections ne forment pas un gabarit à remplir. Omettre toute section qui
n'apporte pas une information distincte. Pour une vidéo simple, `En bref` et
quelques points clés peuvent suffire ; pour une vidéo dense, utiliser plusieurs
sections et, si nécessaire, des sous-sections.

Une citation est facultative. Ne l'utiliser que si sa formulation exacte est
fiable ; ne jamais reconstruire ou améliorer une phrase pour en faire une
citation.

Adapter l'organisation au contenu : thèmes et positions pour une interview,
étapes essentielles pour un tutoriel, arguments et réponses pour un débat,
concepts et relations pour un cours, méthode et résultat pour une démonstration
technique.

## Style et remise du résultat

- Employer un Markdown naturel, précis et facile à parcourir.
- Préférer des titres descriptifs et des phrases informatives.
- Ne pas mentionner la transcription ni le processus de production.
- Lorsque le résumé est le livrable final, ne retourner que le résumé.
- Lorsqu'il s'agit d'une étape intermédiaire, transmettre le résumé à la tâche
  appelante dans le format attendu par celle-ci.
