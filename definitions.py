import numpy as np
import time
import os
import matplotlib.pyplot as plt
import pyfits
import glob

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

setup_default = 'setup_base.ini'
skymodel_default = 'sky40000.osm'
telescope_default = 'telescope_225stations.tm'

#Modify setup file
def set_settings (settings_file_path, key, value):
    os.system('oskar_settings_set %s %s %s'%(settings_file_path, key, value))

#Obtain a settings parameter as a string
def get_settings (settings_file_path, key):
    value = os.popen('oskar_settings_get %s %s'%(settings_file_path, key)).read()
    return value.rstrip('\n')

#Create skymodel
def make_skymodel (skymodel, fov=20, phase_centre_ra_deg=20.0, phase_centre_dec_deg=-30.0, gridsize = 200):
    n = gridsize-1
    gridstep_deg = fov/n
    ra_range = [(phase_centre_ra_deg - fov/2. + j*gridstep_deg) for j in range(n+1)]
    dec_range = [(phase_centre_dec_deg - fov/2. + j*gridstep_deg) for j in range(n+1)]

    #Copy header to sky model
    os.system("cp sky_header.osm %s"%skymodel)

    #Open sky model to write into
    f = open(skymodel, 'a')
    
    #Write to sky model
    for ra in ra_range:
        for dec in dec_range:
            f.write("%f %f 1 0 0 0 100.0e6 -0.7 0 0 0 0\n"%(ra,dec))
   
    f.close()

# Given multifrequency fitsfile, extract first plane and subtract minimum pixel value to all pixels to make an all-positive skymodel
def make_positive_skymodel_and_freq_slice_from_multifreq_fitsfile(skymodel=None, fitsfile=None, img_filename = None, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=3):

    hdulist = pyfits.open('%s'%fitsfile)
    #Extract first frequency slice
    scidata = hdulist[0].data[0]
    header = hdulist[0].header

    hdulist.close()
    
    #Find minimum pixel intensity
    min_pixel = np.min(scidata)

    img_shape = scidata.shape
    
    cellsize_deg = cellsize_arcmin/60.
    extent_deg = cellsize_deg*scidata.shape[1]

    #Copy header to sky model
    os.system("cp sky_header.osm %s"%skymodel)

    # Set pixelval to scidata
    pixelval = scidata

    #Open sky model to write into
    f = open(skymodel, 'a')
    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            ra = phase_centre_ra_deg - extent_deg/2 + cellsize_deg*i
            dec = phase_centre_dec_deg - extent_deg/2 + cellsize_deg*j
            pixelval[i,j] = scidata[i,j] - min_pixel
            f.write("%f %f %f 0 0 0 115.0e6 0 0 0 0 0\n"%(ra,dec,pixelval[i,j]))
    f.close()
   
    os.system('rm %s.fits'%img_filename)

    #Create fitsfile of frequency slice
    hdu = pyfits.PrimaryHDU(pixelval)
    hdu.writeto('%s.fits'%img_filename)

    hdulist = pyfits.open('%s.fits'%img_filename,'update')
    hdulist[0].header = header

    hdulist[0].header['NAXIS'] = 2
    hdulist[0].header['BUNIT'] = 'JY/PIXEL'

    hdulist[0].header['CTYPE1'] = 'RA---SIN'
    hdulist[0].header['CRPIX1'] = hdulist[0].header['NAXIS1']/2 + 1
    hdulist[0].header['CRVAL1'] = phase_centre_ra_deg
    hdulist[0].header['CDELT1'] = -cellsize_deg
    hdulist[0].header['CUNIT1'] = 'deg'

    hdulist[0].header['CTYPE2'] = 'DEC--SIN'
    hdulist[0].header['CRPIX2'] = hdulist[0].header['NAXIS2']/2 + 1
    hdulist[0].header['CRVAL2'] = phase_centre_dec_deg
    hdulist[0].header['CDELT2'] = cellsize_deg
    hdulist[0].header['CUNIT2'] = 'deg'

    hdulist[0].header['CTYPE3'] = 'FREQ'
    hdulist[0].header['CRPIX3'] = 1
    hdulist[0].header['CRVAL3'] = 115000000
    hdulist[0].header['CDELT3'] = 500000
    hdulist[0].header['CUNIT3'] = 'Hz'

    hdulist[0].header['BMAJ'] = cellsize_deg
    hdulist[0].header['BMIN'] = cellsize_deg
    hdulist[0].header['BPA'] = 0. 

    #hdulist[0].header['WSCNORMF'] = 1.0

    hdulist.flush()


# Given multifrequency fitsfile, extract first plane and subtract minimum pixel value from all pixels
def make_positive_freq_slice_from_multifreq_fitsfile(fitsfile=None, img_filename = None, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=3):

    hdulist = pyfits.open('%s'%fitsfile)
    #Extract first frequency slice
    scidata = hdulist[0].data[0]
    header = hdulist[0].header

    hdulist.close()
    
    #Find minimum pixel intensity
    min_pixel = np.min(scidata)

    img_shape = scidata.shape
    
    cellsize_deg = cellsize_arcmin/60.
    extent_deg = cellsize_deg*scidata.shape[1]

    # Set pixelval to scidata
    pixelval = scidata

    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            ra = phase_centre_ra_deg - extent_deg/2 + cellsize_deg*i
            dec = phase_centre_dec_deg - extent_deg/2 + cellsize_deg*j
            pixelval[i,j] = scidata[i,j] - min_pixel

    os.system('rm %s.fits'%img_filename)

    #Create fitsfile of frequency slice
    hdu = pyfits.PrimaryHDU(pixelval)
    hdu.writeto('%s.fits'%img_filename)

    hdulist = pyfits.open('%s.fits'%img_filename,'update')
    hdulist[0].header = header

    hdulist[0].header['NAXIS'] = 2
    hdulist[0].header['BUNIT'] = 'JY/PIXEL'

    hdulist[0].header['CTYPE1'] = 'RA---SIN'
    hdulist[0].header['CRPIX1'] = hdulist[0].header['NAXIS1']/2 + 1
    hdulist[0].header['CRVAL1'] = phase_centre_ra_deg
    hdulist[0].header['CDELT1'] = -cellsize_deg
    hdulist[0].header['CUNIT1'] = 'deg'

    hdulist[0].header['CTYPE2'] = 'DEC--SIN'
    hdulist[0].header['CRPIX2'] = hdulist[0].header['NAXIS2']/2 + 1
    hdulist[0].header['CRVAL2'] = phase_centre_dec_deg
    hdulist[0].header['CDELT2'] = cellsize_deg
    hdulist[0].header['CUNIT2'] = 'deg'

    hdulist[0].header['CTYPE3'] = 'FREQ'
    hdulist[0].header['CRPIX3'] = 1
    hdulist[0].header['CRVAL3'] = 115000000
    hdulist[0].header['CDELT3'] = 500000
    hdulist[0].header['CUNIT3'] = 'Hz'

    hdulist[0].header['BMAJ'] = cellsize_deg
    hdulist[0].header['BMIN'] = cellsize_deg
    hdulist[0].header['BPA'] = 0. 

    #hdulist[0].header['WSCNORMF'] = 1.0

    hdulist.flush()

# Given multifrequency fitsfile, extract one plane
def make_freq_slice_from_multifreq_fitsfile(fitsfile=None, img_filename=None, channel=0, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=1.17):

    hdulist = pyfits.open('%s'%fitsfile)
    #Extract frequency slice - channel numbering starts from 0
    scidata = hdulist[0].data[channel]
    header = hdulist[0].header

    hdulist.close()
    
    cellsize_deg = cellsize_arcmin/60.

    os.system('rm %s'%img_filename)

    #Create fitsfile of frequency slice
    hdu = pyfits.PrimaryHDU(scidata)
    hdu.writeto(img_filename)

    hdulist = pyfits.open(img_filename,'update')
    hdulist[0].header = header

    hdulist[0].header['NAXIS'] = 2
    hdulist[0].header['BUNIT'] = 'JY/PIXEL'

    hdulist[0].header['CTYPE1'] = 'RA---SIN'
    hdulist[0].header['CRPIX1'] = hdulist[0].header['NAXIS1']/2 + 1
    hdulist[0].header['CRVAL1'] = phase_centre_ra_deg
    hdulist[0].header['CDELT1'] = -cellsize_deg
    hdulist[0].header['CUNIT1'] = 'deg'

    hdulist[0].header['CTYPE2'] = 'DEC--SIN'
    hdulist[0].header['CRPIX2'] = hdulist[0].header['NAXIS2']/2 + 1
    hdulist[0].header['CRVAL2'] = phase_centre_dec_deg
    hdulist[0].header['CDELT2'] = cellsize_deg
    hdulist[0].header['CUNIT2'] = 'deg'

    hdulist[0].header['CTYPE3'] = 'FREQ'
    hdulist[0].header['CRPIX3'] = 1
    hdulist[0].header['CRVAL3'] = 115000000+channel*500000
    hdulist[0].header['CDELT3'] = 500000
    hdulist[0].header['CUNIT3'] = 'Hz'

    hdulist[0].header['BMAJ'] = cellsize_deg
    hdulist[0].header['BMIN'] = cellsize_deg
    hdulist[0].header['BPA'] = 0. 

    #hdulist[0].header['WSCNORMF'] = 1.0
    frequency = hdulist[0].header['CRVAL3']

    hdulist.flush()

    return frequency

def make_delta_func_slice_from_multifreq_fitsfile(fitsfile=None, img_filename=None, channel=0, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=1.17):

    hdulist = pyfits.open('%s'%fitsfile)
    #Extract frequency slice - channel numbering starts from 0
    scidata = hdulist[0].data[channel]
    header = hdulist[0].header
    hdulist.close()
    
    scidata = scidata*0
    scidata[hdulist[0].header['NAXIS1']/2,hdulist[0].header['NAXIS2']/2] = 1.0

    cellsize_deg = cellsize_arcmin/60.

    os.system('rm %s'%img_filename)

    #Create fitsfile of frequency slice
    hdu = pyfits.PrimaryHDU(scidata)
    hdu.writeto(img_filename)

    hdulist = pyfits.open(img_filename,'update')
    hdulist[0].header = header

    hdulist[0].header['NAXIS'] = 2
    hdulist[0].header['BUNIT'] = 'JY/PIXEL'

    hdulist[0].header['CTYPE1'] = 'RA---SIN'
    hdulist[0].header['CRPIX1'] = hdulist[0].header['NAXIS1']/2 + 1
    hdulist[0].header['CRVAL1'] = phase_centre_ra_deg
    hdulist[0].header['CDELT1'] = -cellsize_deg
    hdulist[0].header['CUNIT1'] = 'deg'

    hdulist[0].header['CTYPE2'] = 'DEC--SIN'
    hdulist[0].header['CRPIX2'] = hdulist[0].header['NAXIS2']/2 + 1
    hdulist[0].header['CRVAL2'] = phase_centre_dec_deg
    hdulist[0].header['CDELT2'] = cellsize_deg
    hdulist[0].header['CUNIT2'] = 'deg'

    hdulist[0].header['CTYPE3'] = 'FREQ'
    hdulist[0].header['CRPIX3'] = 1
    hdulist[0].header['CRVAL3'] = 115000000+channel*500000
    hdulist[0].header['CDELT3'] = 500000
    hdulist[0].header['CUNIT3'] = 'Hz'

    hdulist[0].header['BMAJ'] = cellsize_deg
    hdulist[0].header['BMIN'] = cellsize_deg
    hdulist[0].header['BPA'] = 0. 

    #hdulist[0].header['WSCNORMF'] = 1.0
    frequency = hdulist[0].header['CRVAL3']

    hdulist.flush()

    return frequency

# Given multifrequency fitsfile, extract first plane and subtract minimum pixel value from all pixels
def make_positive_freq_subcube_from_multifreq_fitsfile(input_fitsfile=None, output_fitsfile=None, start_channel=0, num_channels=1, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=3):

    hdulist = pyfits.open('%s'%input_fitsfile)
    #Extract frequency cube
    scidata = hdulist[0].data[start_channel:start_channel+num_channels]
    header = hdulist[0].header

    hdulist.close()
    
    #Find minimum pixel intensity
    min_pixel = np.min(scidata)

    img_shape = scidata.shape
    
    cellsize_deg = cellsize_arcmin/60.
    extent_deg = cellsize_deg*scidata.shape[1]

    # Set pixelval to scidata
    pixelval = scidata

    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            for k in range(img_shape[2]):
                pixelval[i,j,k] = scidata[i,j,k] - min_pixel

    os.system('rm %s'%output_fitsfile)

    #Create fitsfile of frequency slice
    hdu = pyfits.PrimaryHDU(pixelval)
    hdu.writeto(output_fitsfile)

    hdulist = pyfits.open(output_fitsfile,'update')
    hdulist[0].header = header

    hdulist[0].header['NAXIS'] = 3
    hdulist[0].header['BUNIT'] = 'JY/PIXEL'

    hdulist[0].header['CTYPE1'] = 'RA---SIN'
    hdulist[0].header['CRPIX1'] = hdulist[0].header['NAXIS1']/2 + 1
    hdulist[0].header['CRVAL1'] = phase_centre_ra_deg
    hdulist[0].header['CDELT1'] = -cellsize_deg
    hdulist[0].header['CUNIT1'] = 'deg'

    hdulist[0].header['CTYPE2'] = 'DEC--SIN'
    hdulist[0].header['CRPIX2'] = hdulist[0].header['NAXIS2']/2 + 1
    hdulist[0].header['CRVAL2'] = phase_centre_dec_deg
    hdulist[0].header['CDELT2'] = cellsize_deg
    hdulist[0].header['CUNIT2'] = 'deg'

    hdulist[0].header['CTYPE3'] = 'FREQ'
    hdulist[0].header['CRPIX3'] = 1
    hdulist[0].header['CRVAL3'] = 115000000
    hdulist[0].header['CDELT3'] = 500000
    hdulist[0].header['CUNIT3'] = 'Hz'

    hdulist[0].header['BMAJ'] = cellsize_deg
    hdulist[0].header['BMIN'] = cellsize_deg
    hdulist[0].header['BPA'] = 0. 

    #hdulist[0].header['WSCNORMF'] = 1.0

    hdulist.flush()

def make_empty_skymodel_from_fitsfile(fitsfile=None, skymodel=None, phase_centre_ra_deg=0, phase_centre_dec_deg=-26.7, cellsize_arcmin=3):
        
    hdulist = pyfits.open('%s'%fitsfile)
    #Extract first frequency slice
    scidata = hdulist[0].data[0]
    header = hdulist[0].header

    hdulist.close()

    img_shape = scidata.shape
    
    cellsize_deg = cellsize_arcmin/60.
    extent_deg = cellsize_deg*scidata.shape[1]

    #Copy header to sky model
    os.system("cp sky_header.osm %s"%skymodel)

    #Open sky model to write into
    f = open(skymodel, 'a')
    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            ra = phase_centre_ra_deg - extent_deg/2 + cellsize_deg*i
            dec = phase_centre_dec_deg - extent_deg/2 + cellsize_deg*j
            f.write("%f %f 0 0 0 0 115.0e6 0 0 0 0 0\n"%(ra,dec))
    f.close()

def make_skymodel_from_fitsfile(skymodel=None, fitsfile=None):
 
    os.system('oskar_fits_image_to_sky_model %s %s'%(fitsfile, skymodel))

def make_skymodel_from_fitsfile_manual(skymodel, fitsfile, phase_centre_ra_deg, phase_centre_dec_deg, cellsize_arcmin):

    hdulist = pyfits.open('%s'%fitsfile)
    scidata = hdulist[0].data
    
    img_shape = scidata.shape

    cellsize_deg = cellsize_arcmin/60.
    extent_deg = cellsize_deg*scidata.shape[1]

    #Copy header to sky model
    os.system("cp sky_header.osm %s"%skymodel)

    #Open sky model to write into
    f = open(skymodel, 'a')
  
    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            ra = phase_centre_ra_deg - extent_deg/2 + cellsize_deg*i
            dec = phase_centre_dec_deg - extent_deg/2 + cellsize_deg*j
            f.write("%f %f %f 0 0 0 115.0e6 0 0 0 0 0\n"%(ra,dec,scidata[i,j]+19.))

    f.close()

def make_station(station, num_antennas, radius):
    #'station' is name of station directory
    #'num_antennas' is the number of antennas in a station
    #'radius' is the radius (in m) of the station

    spacing = np.sqrt((np.pi)*radius**2/num_antennas)
    m = int(np.ceil(2*radius/spacing))

    #Arrays containing x and y coordinates of antenna positions
    x_range = []
    y_range = []

    #Extent in x and y directions of antennas
    x_extent = [(-radius + j*spacing) for j in range(m+1)]
    y_extent = [(-radius + j*spacing) for j in range(m+1)]

    for x in x_extent:
        for y in y_extent:
            if np.sqrt(x**2+y**2) <= radius + spacing/2:
                x_range.append(x)
                y_range.append(y)
       
    #Delete station directory if it exists
    try:   
        os.system('rm -rf %s'%station)
    except OSError:
        pass

    #Create station directory
    os.system('mkdir %s'%station)
    #Open layout file to write into
    f = open('%s/layout.txt'%station, 'a')
 
    #Write to layout file
    f.write("%f, %f\n"%(0.000,0.000))
    for i in range(len(x_range)):
            f.write("%0.3f, %0.3f\n"%(x_range[i],y_range[i]))

    #Close layout file
    f.close()

    return (x_range, y_range)


#Create telescope
def make_telescope (telescope, num_stations, radius, width, station_directory):
    #'telescope' is the name of the telescope directory
    #'num_stations' is the number of stations in the array   
    #'radius is the distance (in m) of the furthest station from the center of the array
    #'width' is the standard deviation (in m) of the Gaussian describing the distribution of stations in the array  
    #'station_directory' is the name of the station directory from which the station layout will be obtained

    #Arrays containing x and y coordinates of station positions
    x_range = []
    y_range = []

    #Station count
    n = 0

    while n<num_stations-1:
        x = np.random.normal(0,width)
        y = np.random.normal(0,width)
        if np.sqrt(x**2+y**2) < radius:
            x_range.append(x)
            y_range.append(y)
            n = n+1
     
    #Delete telescope directory if it exists
    try:   
        os.system('rm -rf %s'%telescope)
    except OSError:
        pass

    #Create telescope directory
    os.system('mkdir %s'%telescope)
    #Open layout file to write into
    f = open('%s/layout.txt'%telescope, 'a')
 
    #Write to layout file
    f.write("%f, %f\n"%(0.000,0.000))
    for i in range(num_stations-1):
        f.write("%0.3f, %0.3f\n"%(x_range[i],y_range[i]))

    #Close layout file
    f.close()

    #Total number of stations
    i = num_stations

    if i<=10:
        for j in range(i):
            os.system('cp -r %s %s/station00%s'%(station_directory, telescope, str(j)))
    if i>10 and i<=100:
        for j in range(10):
            os.system('cp -r %s %s/station00%s'%(station_directory, telescope, str(j))) 
        if range(10,i):
            for j in range(10,i):
                os.system('cp -r %s %s/station0%s'%(station_directory, telescope, str(j)))
    if i>100:
        for j in range(10):
            os.system('cp -r %s %s/station00%s'%(station_directory, telescope, str(j))) 
        for j in range(10,100):
                os.system('cp -r %s %s/station0%s'%(station_directory, telescope, str(j)))
        if range(100,i):
            for j in range(100,i):
                os.system('cp -r %s %s/station%s'%(station_directory, telescope, str(j)))
    return (x_range, y_range)

#Create visibilities 
def make_visibilities(setup):
    os.system('oskar_sim_interferometer %s'%setup)

#Create visibilities in measurement set format
def make_visibilities_ms_old(setup):
    os.system('oskar_sim_interferometer %s'%setup)
    vis_file = get_settings(setup, 'interferometer/oskar_vis_filename')
    vis_file_prefix = vis_file.rstrip('.vis')
    convert_oskar_visibilities_to_ms(vis_file, '%s.ms'%vis_file_prefix)

#Create visibility file at a given frequency and for a given time range, given gain errors
def make_visibilities_ms(setup, telescope_directory, start_time, time_interval, duration, output_ms, gain_errors=None):

    #Gain errors is an array of size num_timesteps x num_antennas
    #start_time is in yyyy-M-dTh:m:s format
    #time_interval is in integer minutes
    #duration is total observation time

    num_timesteps = int(duration/time_interval)
    time = start_time #initialize time
    #Create visibilities one time step at a time
    set_settings (setup, 'observation/num_time_steps', 1)
    #Create directory to store visibility files for different times
    os.system('mkdir -p vis_mt')
    os.system('rm vis_mt/*')

    for t in range(num_timesteps):
        time = np.datetime64(time) + np.timedelta64(int(time_interval), 'm')
        set_settings (setup, 'observation/start_time_utc', time)
        set_settings(setup, 'interferometer/oskar_vis_filename', 'vis_mt/vis_%s.vis'%t)

        if gain_errors is not None:
            gains = [gain_errors[0][t], gain_errors[1][t], 0*gain_errors[0][t], 0*gain_errors[0][t]]
        if gain_errors is None:
            gains = None
    
        add_gain_errors(telescope_directory, gains)
        os.system('oskar_sim_interferometer -q %s'%setup)

    os.system('oskar_vis_to_ms vis_mt/* -o %s'%output_ms)
    os.system('rm vis_mt/*')
 
def make_image(setup):
    os.system('oskar_imager %s'%setup)

def make_image_wsclean(ms=None, imgsize=256, cellsize_arcmin=3, niter=0, threshold=0, pol='I', channelsout=1, intervalsout=1, img_filename=None):
    os.system('wsclean -size %d %d -scale %famin -niter %d -threshold %f -pol %s -channelsout %d -intervalsout %d -mgain 0.8 -make-psf -weight natural -gkernelsize 15 -oversampling 1023 -name %s %s'%(imgsize, imgsize, cellsize_arcmin, niter, threshold, pol, channelsout, intervalsout, img_filename, ms))
    
    # os.system('rm %s.fits'%img_filename)

    # hdulist = pyfits.open('%s-image.fits'%img_filename)
    # scidata = hdulist[0].data
    # if len(scidata.shape)==4 and scidata.shape[0]==1 and scidata.shape[1]==1:
    #     scidata=scidata[0,0] 
    # header = hdulist[0].header   
    # hdulist.close()

    # hdu = pyfits.PrimaryHDU(scidata)
    # hdu.writeto('%s.fits'%img_filename)

    # hdulist = pyfits.open('%s.fits'%img_filename,'update')
    # hdulist[0].header = header
    # del hdulist[0].header['WSCNORMF'] 
    # hdulist.flush()

    #os.system('rm %s-image.fits'%img_filename)
    #os.system('cp %s.fits %s-image.fits'%(img_filename, img_filename))
    #os.system('rm %s.fits'%img_filename)
    #os.system('rm %s-{psf,dirty,image}.fits'%img_filename)

def combine_visibilities_to_ms(filename_pattern, output_ms):
    os.system('oskar_vis_to_ms %s* -o %s'%(filename_pattern, output_ms))

def convert_oskar_visibilities_to_ms(filename, output_ms):
    os.system('oskar_vis_to_ms %s -o %s'%(filename, output_ms))
    
def power_spectrum_from_image(img_filename):
    os.system('rm casa_command_file.py')
    os.system('rm amp_fft_%s'%img_filename)
    f = open('casa_command_file.py', 'a') #Open file for writing casa commands
    f.write('ia.newimagefromfits(infile="%s",outfile="img.im",overwrite="True")\n'%img_filename)
    f.write('ia.open("img.im")\n')
    f.write('ia.fft(amp="amp.im")\n')
    f.write('exportfits("amp.im", "amp_fft_%s")\n'%img_filename)
    f.write('ia.close()\n')
    #f.write('ia.removefile("img.im")\n')
    #f.write('ia.removefile("amp.im")\n')
    #f.close()
    
    f.write('os.system("rm -rf img.im")\n')
    f.write('os.system("rm -rf amp.im")\n')

    f.close()
   
    os.system('casa --nologger --log2term -c casa_command_file.py')

def add_gain_errors(telescope_directory, gain_errors=None):
    
    if gain_errors is None:
        G_0 = 1.
        phi_0 = 0.
        G_std = 0.
        phi_std = 0.

    if gain_errors is not None:
        G_0 = gain_errors[0]
        phi_0 = gain_errors[1]
        G_std = gain_errors[2]
        phi_std = gain_errors[3]

    #print G_0.shape

    directory_contents = glob.glob('%s/*'%telescope_directory)
    stations = [item for item in directory_contents if item[-3:]!='txt'] 
    
    for stn in range(len(stations)):
        
        station = stations[stn]
        #print stn, station, stations
        num_antennas = os.popen('wc -l %s/layout.txt'%station).read()
        num_antennas = int(num_antennas.split()[0])    
        
        os.system('rm %s/*gain_phase.txt*'%station)

        f = open('%s/gain_phase.txt'%station, 'w')

        for ant in range(num_antennas):
            #print ant, stn
            if gain_errors is None:
                f.write('%f %f %f %f\n'%(G_0, phi_0, G_std, phi_std))
            if gain_errors is not None:
                f.write('%f %f %f %f\n'%(G_0[stn][ant], phi_0[stn][ant], G_std[stn][ant], phi_std[stn][ant]))

        f.close()


#Generate correlated gain errors
def generate_correlated_gain_errors(rms_gain, timescale, timestep, duration, num_antennas, num_stations):

    print 'RMS gain function:', rms_gain

    # The kernel shape for the correlations
    kernel = rms_gain**2 * Matern(length_scale=timescale)

    gp = GaussianProcessRegressor(kernel=kernel)

    num_timesteps = int(duration/timestep)

    # Create time vector 
    timev = np.linspace(0, duration, num_timesteps)

    # Create num_antennas realizations
    samples_real = gp.sample_y(timev[:, np.newaxis], [num_antennas, num_stations])
    samples_imag = gp.sample_y(timev[:, np.newaxis], [num_antennas, num_stations])

    gain_complex = (1.0+samples_real)+1j*samples_imag

    gain_amplitude = np.abs(gain_complex)
    gain_phase = np.angle(gain_complex)

    gain = [gain_amplitude, gain_phase]

    return gain

#Generate uncorrelated gain errors
def generate_uncorrelated_gain_errors(rms_gain, timestep, duration, num_antennas, num_stations):
    # Number of time steps 
    num_timesteps = int(duration/timestep)

    # Create num_antennas realizations
    samples_real = np.random.normal(0, rms_gain, [num_timesteps, num_stations, num_antennas])
    samples_imag = np.random.normal(0, rms_gain, [num_timesteps, num_stations, num_antennas])

    gain_complex = (1.0+samples_real)+1j*samples_imag

    gain_amplitude = np.abs(gain_complex)
    gain_phase = np.angle(gain_complex)

    gain = [gain_amplitude, gain_phase]
    return gain

def add_noise(telescope_directory, frequencies, rms):

    directory_contents = glob.glob('%s/*'%telescope_directory)
    stations = [item for item in directory_contents if item[-3:]!='txt'] 
    
    os.system('rm %s/*noise_frequencies.txt*'%telescope_directory)
    f = open('%s/noise_frequencies.txt'%telescope_directory, 'w')
    for i in range(len(frequencies)):
        f.write('%f \n'%frequencies[i])
        f.close()

    for stn in stations:
        os.system('rm %s/*rms.txt*'%stn)
        f = open('%s/rms.txt'%stn, 'w')
        for i in range(len(frequencies)):
            f.write('%f \n'%rms[i])

        f.close()

def add_images(image1, image2, difference_image):

    hdulist1 = pyfits.open(image1)
    scidata1 = hdulist1[0].data
    hdulist1.close()

    hdulist2 = pyfits.open(image2)
    scidata2 = hdulist2[0].data
    hdulist2.close()

    scidata = scidata1 + scidata2

    os.system('cp %s %s'%(image1, difference_image))

    hdulist = pyfits.open(difference_image,'update')
    hdulist[0].data = scidata
    hdulist.flush()

def subtract_images(image1, image2, difference_image):

    hdulist1 = pyfits.open(image1)
    scidata1 = hdulist1[0].data
    hdulist1.close()

    hdulist2 = pyfits.open(image2)
    scidata2 = hdulist2[0].data
    hdulist2.close()

    scidata = scidata1 - scidata2

    os.system('cp %s %s'%(image1, difference_image))

    hdulist = pyfits.open(difference_image,'update')
    hdulist[0].data = scidata
    hdulist.flush()

def scale_factor_jy_per_pixel(pixel_spacing_arcmin, frequency):

    #Images in kelvin units
    fg_image_k = 'fg_image_1.17arcmin.fits'
    eor_image_k = 'eor_image_1.17arcmin.fits'

    #Compute pixel area in steradians

    pixel_solid_angle_deg = (pixel_spacing_arcmin/60)**2
    pixel_solid_angle_steradians = pixel_solid_angle_deg * (np.pi/180)**2
         
    k_B = 1.38064852*1e-23 #Boltzmann constant
    c = 3.e8 #Speed of light
 
    freq = frequency #Frequency in Hz
    wavelength = c/freq

    #Compute scale factor to go from K to Jy/pixel
    #See https://science.nrao.edu/facilities/vla/proposing/TBconv
    scale_factor = 2*k_B*pixel_solid_angle_steradians/wavelength**2 #SI units
    jy = 1.e-26 #Definition of Jy in SI units
    scale_factor = scale_factor/jy #Scale factor to go from K to jy/pixel

    return scale_factor

def scale_image(image, scale_factor, scaled_image):

    hdulist = pyfits.open(image)
    scidata = hdulist[0].data
    hdulist.close()

    scidata_new = scale_factor*scidata

    os.system('cp %s %s'%(image, scaled_image))

    hdulist = pyfits.open(scaled_image,'update')
    hdulist[0].data = scidata_new
    hdulist.flush()

def plot_data (x, y, plot_format='o', xlabel=None, ylabel=None, title=None, filename=None):
    plt.plot(x, y, '%s'%plot_format)
    if xlabel:
        plt.xlabel('%s'%xlabel)
    if ylabel:
        plt.ylabel('%s'%ylabel)
    if title:
        plt.title('%s'%title)
    if filename:
        plt.savefig('%s'%filename)
        plt.close()
    else:
        plt.show()

def plot_stations(telescope, filename):
    #Open layout file
    f = open('%s/layout.txt'%telescope, 'r')
    station_positions = f.readlines()
    f.close()

    station_positions =  [sp.rstrip('\n') for sp in station_positions]

    x_pos_station = [float(sp.split(',')[0]) for sp in station_positions]
    y_pos_station = [float(sp.split(',')[1]) for sp in station_positions]
        
    plot_data(x_pos_station, y_pos_station, 'o', 'x position (in m)', 'y position (in m)', 'Station positions', '%s'%filename)

class simulation:
    
    #Initialize simulation
    def __init__(self, setup, telescope, skymodel):
        self.setup = setup
        self.skymodel = skymodel  
        self.telescope = telescope

    def set_defaults(self):
        os.system('cp %s %s'%(setup_default, self.setup))
        os.system('cp %s %s'%(skymodel_default, self.skymodel))
        os.system('cp -r %s %s'%(telescope_default, self.telescope))
 
    #Modify values of settings in setup file
    def modify_setup(self, key, value):      
        set_settings(self.setup, key, value)

    #Create skymodel
    #gridsize is number of sources along one dimension of the grid; total number of sources is gridsize*gridsize
    def create_skymodel(self, fov=20, phase_centre_ra_deg=20.0, phase_centre_dec_deg=-30.0, gridsize = 200):
        make_skymodel(self.skymodel, fov, phase_centre_ra_deg, phase_centre_dec_deg, gridsize)

    #Create telescope
    #Stations is the total number of stations in the telescope. The number density of the stations follows a normal distribution with width=width and spread out to a maximum radius=radius. The stations have identical distribution of antennas specified by the layout file in the station directory.
    def create_telescope(self, num_stations=200, radius = 2000.0, width=500.0, station_directory='station_base'):
        make_telescope(self.telescope, num_stations, radius, width, station_directory)
 
    #Simulate visibilities
    def create_visibilities(self):
        make_visibilities(self.setup)

    #Compute simulation time
    def compute_sim_time(self):
        t1 = time.time()
        make_visibilities(self.setup)
        t2 = time.time()
        return(t2-t1)

#Average beam over stations
def average_beam_over_stations(list_beam_files, average_beam_file):

    scidata_list = []

    for beam in list_beam_files:
        hdulist = pyfits.open(beam)
        scidata = hdulist[0].data
        scidata_list.append(scidata)
        hdulist.close()

    average_beam = sum(scidata_list)/len(scidata_list)
    os.system('cp %s %s'%(list_beam_files[0], average_beam_file))

    hdulist = pyfits.open(average_beam_file,'update')
    hdulist[0].data = average_beam
    hdulist.flush()
