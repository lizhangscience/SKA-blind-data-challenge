from definitions import *
import numpy as np

if __name__ == "__main__":
    
    #Images in kelvin units
    fg_image_k = 'fg_image_1.17arcmin.fits'
    eor_image_k = 'eor_image_1.17arcmin.fits'

    #Compute pixel area in steradians
    pixel_spacing_arcmin = 1.17 
    pixel_solid_angle_deg = (pixel_spacing_arcmin/60)**2
    pixel_solid_angle_steradians = pixel_solid_angle_deg * (np.pi/180)**2
         
    k_B = 1.38064852*1e-23 #Boltzmann constant
    c = 3.e8 #Speed of light
 
    freq = 115.e6 #Frequency in Hz
    wavelength = c/freq

    #Compute scale factor to go from K to Jy/pixel
    #See https://science.nrao.edu/facilities/vla/proposing/TBconv
    scale_factor = 2*k_B*pixel_solid_angle_steradians/wavelength**2 #SI units
    jy = 1.e-26 #Definition of Jy in SI units
    scale_factor = scale_factor/jy #Scale factor to go from K to jy/pixel

    #Create fg, eor, and fg+eor images in units of Jy/pixel
    scale_image('fg_image_1.17arcmin.fits', scale_factor, 'fg_image_jy_per_px.fits')
    scale_image('eor_image_1.17arcmin.fits', scale_factor, 'eor_image_jy_per_px.fits')
    add_images('fg_image_jy_per_px.fits', 'eor_image_jy_per_px.fits', 'fg_plus_eor_image_jy_per_px.fits')

    #Create skymodels from these images
    make_skymodel_from_fitsfile(fitsfile='fg_image_jy_per_px.fits', skymodel='fg_image_jy_per_px.osm')
    make_skymodel_from_fitsfile(fitsfile='eor_image_jy_per_px.fits', skymodel='eor_image_jy_per_px.osm')
    make_skymodel_from_fitsfile(fitsfile='fg_plus_eor_image_jy_per_px.fits', skymodel='fg_plus_eor_image_jy_per_px.osm')
