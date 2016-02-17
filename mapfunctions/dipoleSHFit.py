#!/usr/bin/env python

import healpy as hp
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import quad
import os, glob, ROOT, time
import matplotlib.pyplot as plt
from matplotlib import rc
from mapFunctions import getFitParams, outputFit, multifit
from dipolePlot import getDipole
import argparse
from energyCuts import getEnergyMaps

rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
rc('text', usetex=True)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
            description='description: Plotting program for healpix maps.')
    
    parser.add_argument('-f','--filepath', help='Path to healpix fit file to be analyzed')
    parser.add_argument('-m', '--min', dest='min', help='Plot minimum value')
    parser.add_argument('-M', '--max', dest='max', help='Plot maximum value')
    parser.add_argument('-d', '--decmin', dest='decmin', type=float,
            default=-90., help='Minimum declination value (90->-90)')
    parser.add_argument('-D', '--decmax', dest='decmax', type=float,
            default=-25., help='Maximum declination value (90->-90)')
    parser.add_argument('-r', '--ramin', dest='ramin', type=float,
            help='Minimum RA value')
    parser.add_argument('-R', '--ramax', dest='ramax', type=float,
            help='Maximum RA value')
    parser.add_argument('--mask', dest='mask', default=False, 
            action='store_true', help='Intelligent masking')
    parser.add_argument('-b', '--batchmode', action='store_true', dest='batch',
            default=False, help='Execute without interaction')
    parser.add_argument('-o', '--output', dest='output', action='store_true',
            default=False, help='Output image file')
    parser.add_argument('-n', '--mapName', dest='mapName',
            help='Map type desired (signal, relint, relint_err, data, bg)')
    parser.add_argument('-s', '--scale', dest='scale', type=float,
            help='Scale the map after input')
    parser.add_argument('-S', '--smooth', dest='smooth', type=float, default=0,
            help='Desired smoothing radius (in degrees)')
    parser.add_argument('--stype', dest='stype', default='tophat',
            help='Option for smoothing type [tophat|gauss]')
    parser.add_argument('--swindow', dest='swindow', type=float, default=3,
            help='Option for smoothing window')
    parser.add_argument('--lmax', dest='lmax', type=int, default=1,
            help='Highest l value to be fit. (l=1: dipole, l=2: quadrupole, etc.)')
    parser.add_argument('--fix_multi', dest='fix_multi',
            default=False, action='store_true',
            help='Fix multipole subtraction to values from cumulative map')
    parser.add_argument('-x', '--threshold', dest='threshold', type=float,
            help='Threshold value for plotting data')
    parser.add_argument('-c', '--coords', dest='coords', default='C',
            help='C=equatorial, G=galactic, E=ecliptic')
    parser.add_argument('--gplane', dest='gplane',
            default=False, action='store_true',
            help='Show the galactic plane')
    parser.add_argument('--half', action="store_true", dest='half',
            default=False, help='Show only bottom half of the sky')
    parser.add_argument('--title', action="store_true", dest="title",
            default=False, help='Show the title on the plot')
    parser.add_argument('--outDir', dest='outDir',
            default='/home/jbourbeau/public_html/figures/SH-fit/',
            help='Option for changing output directory')
    parser.add_argument('--prelim', action='store_true', dest='prelim',
            default=False, help='Indicate plot is preliminary')
    parser.add_argument('--llabel', dest='llabel',
            default=False, help='Optional left label overlay on map')
    parser.add_argument('--rlabel', dest='rlabel',
            default=False, help='Optional right label overlay on map')
    parser.add_argument('--polar', dest='polar',
            default=False, action='store_true',
            help='Polar gnomonic view of map')
    parser.add_argument('--customOut', dest='customOut',
            help='Option for custom output file name')
    parser.add_argument('--ext', dest='ext',
            default='png', help='Output file extension')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
            default=False, help='Verbose output')
    parser.add_argument('--params', action='store_true', dest='params',
            default=True, help='Print params')
    parser.add_argument('--usefit', action='store_true', dest='usefit',
            default=False, help='Use spherical harmonic fits instead of raw data')
    parser.add_argument('--plotname', dest='plotname',
            help='Output plot filename')
    parser.add_argument('--noshow', action='store_true', dest='noshow',
            default=False, help='Do not display plots')


    args = parser.parse_args()
    opts = vars(args).copy()
    #print('opts = {}'.format(opts))
   
    alpha = 1/20.
    config = 'IC'
    maps = getEnergyMaps(config)
    energy_bin_median = [4.12, 4.38, 4.58, 4.85, 5.12, 5.38, 5.77, 6.13, 6.73]
    energy_err_lower = [0.62, 0.65, 0.68, 0.73, 0.74, 0.75, 0.6, 0.52, 0.46]
    energy_err_upper = [0.5, 0.54, 0.55, 0.64, 0.72, 0.78, 0.83, 0.63, 0.58]

    # Produce dipole expansion coeeficient plot
    #fig = plt.figure(1)
    labels = [r'$l=1$',r'$l=2$',r'$l=3$']
    #for i in range(1):
    for l in range(1,args.lmax+1):
        amplitude = []
        amplitude_err = []
        phase = []
        phase_err = []
        for i in range(len(maps)):
            # Read in (multiple) input files
            data, bg, local = np.sum([hp.read_map(f, range(3), verbose=False)\
                    for f in maps[i]], axis=0)
            p = multifit(l, data, bg, alpha, **opts)
            #print('p = {}'.format(np.sqrt(p['Y(1,0)']**2+p['Y(1,1)']**2+p['Y(1,-1)']**2)))
            dipole = getDipole(p)
            #print('dipole = {}'.format(dipole))
            #print('dipole[0] = {}'.format(dipole[0]))
            amplitude.append(dipole[0])
            amplitude_err.append(dipole[1])
            phase.append(dipole[2])
            phase_err.append(dipole[3])
            
        fig = plt.figure(l)
        plt.errorbar(energy_bin_median,amplitude,xerr=[energy_err_lower,energy_err_upper],\
                yerr=amplitude_err,marker='.',markersize=10,linestyle='None')
        plt.title(r'$l_{} = $ {}'.format('{max}',l))
        ax = fig.axes[0]
        ax.axis('on')
        tPars = {'fontsize':16}
        ax.set_xlim(3.5,7.5)
        #ax.set_ylim(0.0,0.0016)
        ax.set_ylim(0.0,0.004)
        ax.set_ylabel(r'$\Delta N/\langle N \rangle$', **tPars)
        ax.set_xlabel(r'log$_{10}$(E/GeV)', **tPars)
        #plt.legend()
        if args.output:
            plt.savefig(args.outDir+'amplitude_lmax{}'.format(l)+'.'+args.ext, dpi=300, bbox_inches='tight')
        
    '''if args.output:
        if args.plotname:
            outFile  = args.outDir + args.plotname
        else:
            if args.lmax == 1:
                name = 'phase_dipolefit'
            elif args.lmax == 2:
                name = 'phase_quadrupolefit'
            elif args.lmax == 3:
                name = 'phase_octupolefit'
            else:
                name = 'phase_data'
            outFile  = args.outDir + name
        plt.savefig(outFile+'.'+args.ext, dpi=300, bbox_inches='tight')'''
    
    if not args.noshow:
        plt.show()








    
