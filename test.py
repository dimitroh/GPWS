import math, matplotlib.pyplot as plt, matplotlib, numpy as np
from matplotlib.patches import Polygon, Circle
from matplotlib.collections import PatchCollection
import gpws

from ivy.std_api import *
import sys, logging
logger = logging.getLogger('Ivy')
from optparse import OptionParser

from copy import copy

def ftmin_to_ms(vz):
    return 0.00508*vz

def ft_to_m(z):
    return 0.3048*z

def plot_mode(mode, fig=None, ax=None):
    """
    :param mode: Classe d'un mode
    :return: Dessine les enveloppes d'un mode
    """
    if fig == None and ax==None:
        fig, ax = plt.subplots()
    patches = []

    for env in mode.list_enveloppes:
        polygon = Polygon(env.vertexes, True)
        patches.append(polygon)
    p = PatchCollection(patches,  alpha=0.2)

    colors = [i for i in range(len(mode.list_enveloppes))]
    p.set_array(np.array(colors))

    ax.add_collection(p)
    plt.autoscale()
    if fig == None and ax==None:
        plt.show()

def plot_trajectory(traj, modes, flaps, gear, gamma, phase, mode_test_name):
    """
    :param traj: liste d'etats
    :param modes: liste de modes
    :param flaps : configuration volets de l'avion
    :param gear : configuration train d'atterrissage de l'avion
    :param gamma : pente de l'avion
    :param phase : phase de vol de l'avion
    :param mode_test_name : nom du mode pour lequel la liste d'etats a ete creee pour le tester
    :return: Plot les points de la trajectoire de la forme associee a l'enveloppe dans laquelle ils se trouvent
    """

    fig, ax = plt.subplots()
    fig.text(0.3, 0.95, u'Test du {0} - flaps : {1} | gear : {2} | phase : {3} | gamma : {4}'.format(mode_test_name,flaps, gear, phase, math.degrees(gamma)), fontsize=15)
    number_of_lines = math.ceil(float(len(modes)) / 3)
    number_of_columns = math.ceil(float(len(modes)) / number_of_lines)

    markers = ['o', 'v', '^', '<', '>', '8', 's', 'p']
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

    for i in range(len(modes)):
        ax = plt.subplot(number_of_lines, number_of_columns, i+1)
        mode = modes[i]
        plot_mode(mode, fig ,ax)
        for etat in traj:
            x, y = etat.get_xy(mode)
            env = mode.get_enveloppe((x,y), flaps, gear)
            if env == None:
                marker = markers[0]
                color =  colors[0]
            else:
                i = mode.list_enveloppes.index(env)
                marker = markers[i + 1]
                color= colors[i + 1]
            plt.title(mode.name)
            plt.plot(x, y, marker, color=color)

        nb_env = len(mode.list_enveloppes)
        legends = [plt.Line2D((0,1),(0,0), marker=markers[0], linestyle='', color= colors[0])]
        description = ['Hors enveloppe']
        for i in range(nb_env):
            legends.append(plt.Line2D((0,1),(0,0), marker=markers[i+1], linestyle='', color= colors[i+1]))
            description.append(mode.list_enveloppes[i].name)
        ax.legend(legends, description, prop={'size':8})
        plt.autoscale()
    try :

        plt.show()
    except AttributeError:
        print("Erreur d'affichage")



def segm_test_diag(mode, sens_parcours): #sens_parcours : True de gauche a droite, False de droite a gauche
    """Cree un segment de test sur la 'diagonale'  du mode"""
    (xmin, ymin, xmax, ymax) = mode.get_xmin_ymin_xmax_ymax()
    if sens_parcours:
        x_initial = xmin
        y_inital = ymax + (ymax - ymin) * 0.2
        x_final = xmax - 0.1 *  (xmax - xmin)
        y_final = ymin + 0.1 * (ymax - ymin)
    else:
        x_initial = xmax - 0.1 *  (xmax - xmin)
        y_inital = ymin + 0.1 * (ymax - ymin)
        x_final = xmin
        y_final = ymax + (ymax - ymin) * 0.2
    return x_initial, y_inital, x_final, y_final

def segm_test_rect(mode, position_y, sens_parcours): #position_y : position en ordonnee de la droite par rapport a l'enveloppe #sens_parcours : True de gauche a droite, False de droite a gauche
    """Cree un segment de test 'en ligne droite' du mode"""
    (xmin, ymin, xmax, ymax) = mode.get_xmin_ymin_xmax_ymax()
    if sens_parcours:
        x_initial = xmin
        y_inital = position_y * (ymax - ymin) + ymin
        x_final = xmax - 0.1 *  (xmax - xmin)
        y_final = y_inital
    else:
        x_initial = xmax - 0.1 *  (xmax - xmin)
        y_inital = position_y * (ymax - ymin) + ymin
        x_final = xmin
        y_final = y_inital
    return x_initial, y_inital, x_final, y_final



def create_test(mode, phase, flaps, gear, gamma, absi, absf, ordi, ordf, nb_points, filename, modes_to_plot=None):
    """

    :param mode: le mode a tester, de la classe Mode
    :param flaps : configuration volets de l'avion
    :param gear : configuration train d'atterrissage de l'avion
    :param gamma : pente de l'avion
    :param phase : phase de vol de l'avion
    :param absi, absf : abscisses du point de depart et d'arrivee du segment de test, obtenu a partir d'une fonction segm_test
    :param ordi, ordf : ordonnees du point de depart et d'arrivee du segment de test, obtenu a partir d'une fonction segm_test
    :param nb_points : nombre de points/d'etats du segment de test
    :param filename : nom que l'on donne au fichier de test qui va etre cree
    :param modes_to_plot : liste des modes ou representer graphiquement la liste d'etats de test
    :return cree un fichier texte test donnant une liste d'etats avion a rejouer pour simuler le passage de l'avion dans les enveloppes d'un mode et ainsi le tester
    :return plot la liste d'etats de test (un segment) sur des graphiques representant les enveloppes des modes

    """
    etat = gpws.Etat(15, 5000, 0, 0, None, 0, 0, flaps, gear, phase)
    pas_abs = (absf - absi) / nb_points
    pas_ord = (ordf - ordi) / nb_points
    abs = absi
    ord = ordi
    traj = []
    fic = open(filename, "w")
    for i in range(nb_points):
        etat.set_xy(abs, ord, mode, gamma)
        time = "Time t={}\n".format(i)
        radio_alt =  etat.generate_radioalt()
        statevector = etat.generate_statevector(gamma)
        fms = etat.generate_fms()
        config = etat.generate_config()
        fic.write(time)
        fic.write(radio_alt)
        fic.write(statevector)
        fic.write(fms)
        fic.write(config)
        traj.append(copy(etat))
        abs += pas_abs
        ord += pas_ord
    fic.write("Time t={}\n".format(nb_points))
    fic.close()
    if modes_to_plot == None:
        modes_to_plot = [mode]

    plot_trajectory(traj, modes_to_plot, flaps, gear, gamma, phase, mode.name)

def create_test_global(mode,list_modes, phase, flaps, gear, gamma, nb_points):
    """Automatise le test d'un mode sur plusieurs listes d'etats test en appelant la fonction create_test pour plusieurs pour ces listes d'etats test crees par les fonctions segm_test

    :param mode:le mode a tester, de la classe Mode
    :param list_modes:liste des modes ou representer graphiquement la liste d'etats de test
    :param phase:phase de vol de l'avion
    :param flaps:configuration volets de l'avion
    :param gear:configuration train d'atterrissage de l'avion
    :param gamma:pente de l'avion
    :param nb_points:nombre de points/d'etats du segment de test
    :return:cree quatre fichiers texte test donnant une liste d'etats avion a rejouer pour simuler le passage de l'avion dans les enveloppes d'un mode et ainsi le tester
    :return plot la liste d'etats de test (un segment) sur des graphiques representant les enveloppes des modes

    """
    absi, ordi, absf, ordf = segm_test_rect(mode, position_y = 0.33, sens_parcours = True)
    create_test(mode, phase, flaps, gear, gamma, absi, absf, ordi, ordf, nb_points, filename = mode.name + "_traj_rect_1.txt", modes_to_plot = list_modes)
    plt.close()
    absi, ordi, absf, ordf = segm_test_rect(mode, position_y = 0.13, sens_parcours = True)
    create_test(mode, phase, flaps, gear, gamma, absi, absf, ordi, ordf, nb_points, filename = mode.name + "_traj_rect_2.txt", modes_to_plot = list_modes)
    plt.close()
    absi, ordi, absf, ordf = segm_test_diag(mode, sens_parcours = True)
    create_test(mode, phase, flaps, gear, gamma, absi, absf, ordi, ordf, nb_points, filename = mode.name + "_traj_diag_gd.txt", modes_to_plot = list_modes)
    plt.close()
    absi, ordi, absf, ordf = segm_test_diag(mode, sens_parcours = False)
    create_test(mode, phase, flaps, gear, gamma, absi, absf, ordi, ordf, nb_points, filename = mode.name + "_traj_diag_dg.txt", modes_to_plot = list_modes)
    plt.close()

#parse
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.set_defaults(ivy_bus="127.255.255.255:2010", interval=5, verbose=False, app_name="Test")
parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                  help='Be verbose.')
parser.add_option('-i', '--interval', type='int', dest='interval',
                  help='Interval between messages (in seconds)')
parser.add_option('-b', '--ivybus', type='string', dest='ivy_bus',
                  help='Bus id (format @IP:port, default to 127.255.255.255:2010)')
parser.add_option('-a', '--appname', type='string', dest='app_name',
                  help='Application Name')
(options, args) = parser.parse_args()

# init log
level = logging.INFO
if options.verbose: # update logging level
    level = logging.DEBUG
logger.setLevel(level)



def start_test(nom_fichier_test):
    """

    :param nom_fichier_test:le fichier contenant la liste d'etats test
    :return:des que le time est lance, active la fonction send_fic_test qui simule le vol de l'avion avec la liste d'etats test de nom_fichier_test

    """
    IvyBindMsg(send_fic_test(nom_fichier_test), "^Time t=")

def send_fic_test(nom_fichier_test):
    """

    :param nom_fichier_test: le fichier contenant la liste d'etats test
    :return: simule le vol de l'avion en envoyant sur le bus les etats, le time et la radioaltitude du fichier texte test

    """
    import time
    time.sleep(0.2)
    with open(nom_fichier_test, "r") as fic:
        for line in fic.readlines():
            IvySendMsg(line)
            time.sleep(0.5)


#ivy connection
def on_cx_proc(agent, connected):
    if connected == IvyApplicationDisconnected:
        logger.error('Ivy application %r was disconnected', agent)
    else:
        logger.info('Ivy application %r was connected', agent)


def on_die_proc(agent, _id):
    logger.info('received the order to die from %r with id = %d', agent, _id)


def connect(app_name, ivy_bus):
    IvyInit(app_name,                   # application name for Ivy
            "[%s ready]" % app_name,    # ready message
            0,                          # main loop is local (ie. using IvyMainloop)
            on_cx_proc,                 # handler called on connection/disconnection
            on_die_proc)
    IvyStart(ivy_bus)

connect(options.app_name, options.ivy_bus)



## Mode 2 ##
def test_mode2():
    traj_ord = [1000]
    traj_abs = [2300, 3000, 4000, 5000, 6000]
    etats =  []
    gamma = -10
    for i in range(1, len(traj_abs)):
        traj_ord.append(traj_ord[i-1] - (traj_abs[i] / 60.0))
    for i in range(len(traj_abs)):
        x = traj_abs[i]
        y = traj_ord[i]
        etat = gpws.Etat(100,0,0,0,0,0,0,"0","up",gpws.APP)
        etat.set_xy(x, y, gpws.L_Modes[1])
        etats.append(etat)
    plot_trajectory(etats, [gpws.L_Modes[1]], "0", "up", 0, gpws.APP, "mode2")
    fic = open("test_mode2.txt", 'w')
    for i in range(len(etats)):
        etat = etats[i]
        time = "Time t={}\n".format(i)
        radio_alt =  etat.generate_radioalt()
        statevector = etat.generate_statevector(gamma)
        fms = etat.generate_fms()
        config = etat.generate_config()
        fic.write(time)
        fic.write(radio_alt)
        fic.write(statevector)
        fic.write(fms)
        fic.write(config)
    fic.write("Time t={}\n".format(len(etats)))
#test_mode2()

## Mode 3 ##
def test_mode3():
    traj_ord = [1600, 1630, 1660, 1630, 1600, 1570, 1520, 1490, 1430, 1440, 1420]
    traj_abs = [0, 0, 0, 30, 60, 90, 140, 170, 230, 0, 240]
    etats =  []
    gammas = []
    phase = gpws.TAKEOFF
    for i in range(len(traj_abs)):
        x = traj_abs[i]
        y = traj_ord[i]
        (vz, gamma) = (-10, -10) if (i == 0 or traj_ord[i-1] < traj_ord[i]) else (10, 10)
        gammas.append(gamma)
        etat = gpws.Etat(vz, 0, 0, 0, 0, 0, 0, "0", "up", phase)
        etat.set_xy(x, y, gpws.L_Modes[2], gammas[i])
        etats.append(etat)
    plot_trajectory(etats, gpws.L_Modes, "0", "up", 0, phase, "mode3")
    fic = open("test_mode3.txt", 'w')
    for i in range(len(etats)):
        etat = etats[i]
        time = "Time t={}\n".format(i)
        radio_alt =  etat.generate_radioalt()
        statevector = etat.generate_statevector(gammas[i])
        fms = etat.generate_fms()
        config = etat.generate_config()
        fic.write(time)
        fic.write(radio_alt)
        fic.write(statevector)
        fic.write(fms)
        fic.write(config)
    fic.write("Time t={}\n".format(len(etats)))


#Tests
modes = gpws.L_Modes



## Mode 1 ##
create_test_global(modes[0],gpws.L_Modes, gpws.APP, "0", gpws.DOWN, -10*math.pi/180, 20)
start_test("mode1_traj_diag_gd.txt")

## Mode 2 ##
# test_mode2()
# start_test("test_mode2.txt")

## Mode 3 ##
# test_mode3()
# start_test("test_mode3.txt")

## Mode 4 ##
# create_test_global(modes[3],gpws.L_Modes, gpws.APP, "0", gpws.UP, -10*math.pi/180, 20)
# start_test("mode4_traj_rect_2.txt")

## Mode 6 ##
# create_test_global(modes[5],gpws.L_Modes, gpws.LDG, "0", gpws.DOWN, -10*math.pi/180, 20)
# start_test("mode6_traj_rect_2.txt")

IvyStop()