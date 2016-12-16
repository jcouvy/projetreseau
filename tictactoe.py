# -*- coding: utf-8 -*-
#!/usr/bin/python3

from grid import *
from client import *
from serveur import *
import sys

# _____________________________R E A D M E____________________________________

# Deroulement d'une partie:

# Serveur initialise trois grilles (3x3) pour le Joueur 1, 2 et l'état de la partie (visible par les observateurs).

# Par défaut le Joueur 1 prends la main en premier.
# Extension: Serveur fait un coin-flip pour choisir le premier joueur.

# Le serveur envoie une sequence de bytes indiquant le début de la partie. Chaque client va alors créer un objet de type Grid avec les fonctions de grid.py.

# Exemple: 000000000 le client appelle Grid() qui instancie une grille vide.

# A chaque coup, le serveur distingue donc 3 cas:

# 1- La case a déjà été jouée par l'adversaire (le premier test if (grids[0].cells[shot] != EMPTY): échoue). Le serveur met dans la grille du joueur courant le coup déjà joué par l'adversaire (c.à.d la valeur de la case dans la grille globale).

# 2- Le coup est légal (Grid.play(self, player, selfNum) passe les assert), les grilles côté serveur sont modifiées et le serveur encode dans une séquence l'état de la grille du joueur courant et donne la main à l'adversaire:

# O |   |
# - - - - -
#   |   |     #100000000 est la séquence de bytes envoyée au joueur 1.
# - - - - -   #Ci-contre, la grille générée par J1 après avoir décodé la
#   |   |     #séquence.

# - Le coup est illégal (en dehors des limites de la grille) le serveur renvoie une valeur spéciale demandant au client de ré-itérer son coup.

# A la réception d'une réponse du serveur, les clients décodent la séquence, modifient le contenu de leur grille puis traduisent le résultat en affichage ASCII avec les fonctions de grid.py.

# Tant que le serveur ne détecte pas que la partie est terminée il continue, à chaque coup, d'envoyer une nouvelle séquence décrivant la grille propre de chaque joueur et la grille globale aux observateurs.

# Une fois la partie terminée le serveur envoie un message informant les joueurs du gagnant de la partie. Même chose pour les observateurs.

if __name__ == '__main__':
    if len(sys.argv) == 1:
        start_server()
    if len(sys.argv) == 2:
        start_client(sys.argv[1])
