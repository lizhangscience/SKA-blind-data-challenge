from definitions import *
import numpy as np
import os

if __name__ == "__main__":   

    start_channel = 0
    num_channels = 21
    pixel_spacing_arcmin = 1.17
 
    make_positive_freq_subcube_from_multifreq_fitsfile(input_fitsfile='GalFG_standard.fits', output_fitsfile= 'GalFG_standard_subcube.fits', start_channel=start_channel, num_channels=num_channels, cellsize_arcmin=pixel_spacing_arcmin)

    make_positive_freq_subcube_from_multifreq_fitsfile(input_fitsfile='eor_standard.fits', output_fitsfile= 'eor_standard_subcube.fits', start_channel=start_channel, num_channels=num_channels, cellsize_arcmin=pixel_spacing_arcmin)


    os.system('mkdir -p skymodels_mf') 

    for channel in range(num_channels):

        frequency = make_freq_slice_from_multifreq_fitsfile(fitsfile='GalFG_standard_subcube.fits', img_filename='fg_image_slice.fits', channel=channel, cellsize_arcmin=pixel_spacing_arcmin)
        scale_factor = scale_factor_jy_per_pixel(pixel_spacing_arcmin, frequency)
        scale_image('fg_image_slice.fits', scale_factor, 'fg_image_slice_jy_per_px.fits')
        make_skymodel_from_fitsfile(fitsfile='fg_image_slice_jy_per_px.fits', skymodel='skymodels_mf/fg_image_jy_per_px_%s_Hz.osm'%str(frequency))

        frequency = make_freq_slice_from_multifreq_fitsfile(fitsfile='eor_standard_subcube.fits', img_filename='eor_image_slice.fits', channel=channel, cellsize_arcmin=pixel_spacing_arcmin)
        scale_factor = scale_factor_jy_per_pixel(pixel_spacing_arcmin, frequency)
        scale_image('eor_image_slice.fits', scale_factor, 'eor_image_slice_jy_per_px.fits')
        print frequency, str(frequency)
        make_skymodel_from_fitsfile(fitsfile='eor_image_slice_jy_per_px.fits', skymodel='skymodels_mf/eor_image_jy_per_px_%s_Hz.osm'%str(frequency))

        add_images('fg_image_slice_jy_per_px.fits', 'eor_image_slice_jy_per_px.fits', 'fg_plus_eor_image_slice_jy_per_px.fits')
        make_skymodel_from_fitsfile(fitsfile='fg_plus_eor_image_slice_jy_per_px.fits', skymodel='skymodels_mf/fg_plus_eor_image_jy_per_px_%s_Hz.osm'%str(frequency))


