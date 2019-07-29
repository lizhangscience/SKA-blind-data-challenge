from definitions import *
from pyrap.tables import table
import os
import time

if __name__ == "__main__":

    t1 = time.time()

    ===============================
    Parameter settings
    ===============================

    #Blind challenges directory 
    challenges_directory = '/net/node131/data/users/lofareor/mitra/SKA_blind_challenge'

    #Setup file settings
    setup_file = 'setup_SKA_core_blind_challenge.ini'
    vis_file = 'SKA_core' #visibility filename (prefix) to write visibilities to

    #Telescope configuration 
    num_antennas = 256
    num_stations = 224
    
    #Telescope directory
    telescope_directory = 'SKA_core.tm'     
    #Skymodels directory
    skymodels_directory = 'skymodels_mf'
 
    #Foreground type
    fg_type = 'diffuse'

    #Output directories
    plots_directory = 'blind_challenge/plots/%s'%fg_type
    data_directory = 'blind_challenge/data/%s'%fg_type
    images_directory = 'blind_challenge/images'
    visibilities_directory = 'blind_challenge/visibilities'

    #Imaging parameters
    imgsize = 300 #image size in pixels
    cellsize_arcmin = 2 #pixel spacing   
    fov = imgsize*cellsize_arcmin/60.
 
    #Add frequency and noise files in setup file
    set_settings (setup_file, 'interferometer/noise/enable', 'true')
  
    #Add noise to telescope
    frequencies = np.linspace(115e6, 125e6, 21)

    #Station SEFD in Jy
    sefd_stn_0 = 0.0589
    frequency_0 = frequencies[0]

    quantities = ['fg', 'noise', 'eor', 'eor_p_noise', 'eor_p_fg', 'eor_p_noise_p_fg']

    #Observation time parameters
    start_time = '2015-01-01T06:00:00' #Start time in UTC, in yyyy-M-dTh:m:s format
    timestep = 30 #Time step in minutes
    duration_hr = 4. #Duration of observation in hours
    duration = duration_hr*60 #Convert duration into minutes
    total_obsv_time_hr = [10., 100., 1000.] #Observation time, in hours

    ===============================

    #Create image subdirectories
    img_subdirectory = {'fg':'fg_%s'%fg_type, 'noise':'noise', 'eor':'eor', 'eor_p_noise':'eor_p_noise', 'eor_p_fg':'eor_p_fg', 'eor_p_noise_p_fg':'eor_p_noise_p_fg'}

    #Clean up directories
    for qnt in quantities:
        os.system('rm %s/%s/*'%(images_directory, img_subdirectory[qnt]))

    os.system('rm %s/*'%data_directory)
    os.system('rm -rf %s/*'%visibilities_directory)
 
    #Simulate visibilities and create images for FG, noise, EoR, EoR+noise, EoR+FG, EoR+noise+FG

    for t_obsv in total_obsv_time_hr:
        for qnt in quantities:
            for frequency in frequencies:

                sefd_stn = sefd_stn_0*(frequency_0/frequency)**0.55 #SEFD at this frequency
                sefd_stn = sefd_stn/np.sqrt(t_obsv/duration_hr) #Noise adjusted for total hours of observation

                frequency=[frequency]

                if qnt=='fg': rms = [0.]
                if qnt=='noise': rms = [sefd_stn]
                if qnt=='eor': rms = [0.]
                if qnt=='eor_p_noise': rms = [sefd_stn]
                if qnt=='eor_p_fg': rms = [0.]
                if qnt=='eor_p_noise_p_fg': rms = [sefd_stn]

                #Skymodel filenames for FG and EoR
                #These skymodels cover a 10x10 FOV and the pixel spacing is 1.17 arcmin 
                #FG skymodel filename
                if fg_type == 'diffuse':
                    skymodel_fg_filename = '%s/fg_%s/fg_image_jy_per_px_%s_Hz.osm'%(skymodels_directory, fg_type, str(int(frequency[0])))
                if fg_type == 'point':
                    skymodel_fg_filename = '%s/fg_%s/ScubeSkymodel1mJy.osm'%(skymodels_directory, fg_type)

                #EoR skymodel filename
                skymodel_eor_filename = '%s/eor/eor_image_jy_per_px_%s_Hz.osm'%(skymodels_directory, str(int(frequency[0])))

                #Empty skymodel filename for creating noise-only image
                skymodel_empty_filename = '%s/empty_sky/sky_empty_1.17arcmin.osm'%skymodels_directory

                #EoR + noise filename
                os.system('cat %s %s > eor_p_noise.osm'%(skymodel_eor_filename, skymodel_empty_filename))
                skymodel_eor_p_noise_filename = 'eor_p_noise.osm'

                #EoR + FG filename
                os.system('cat %s %s > eor_p_fg.osm'%(skymodel_eor_filename, skymodel_fg_filename))
                skymodel_eor_p_fg_filename = 'eor_p_fg.osm'

                #EoR + noise + FG filename
                os.system('cat %s %s %s > eor_p_noise_p_fg.osm'%(skymodel_eor_filename, skymodel_empty_filename, skymodel_fg_filename))
                skymodel_eor_p_noise_p_fg_filename = 'eor_p_noise_p_fg.osm'

                skymodel_filename = {'fg':skymodel_fg_filename, 'noise':skymodel_empty_filename, 'eor':skymodel_eor_filename, 'eor_p_noise': skymodel_eor_p_noise_filename, 'eor_p_fg': skymodel_eor_p_fg_filename, 'eor_p_noise_p_fg': skymodel_eor_p_noise_p_fg_filename}   

                add_noise(telescope_directory, frequency, rms)

                set_settings (setup_file, 'sky/oskar_sky_model/file', skymodel_filename['%s'%qnt])   
                set_settings (setup_file, 'observation/start_frequency_hz', frequency[0]) 
                make_visibilities_ms(setup=setup_file, telescope_directory=telescope_directory, start_time=start_time, time_interval=timestep, duration=duration, output_ms='%s.ms'%vis_file)
                os.system('rm -rf %s/%s_%s_Hz_t_obsv_%s_hr.ms'%(visibilities_directory, qnt, str(int(frequency[0])), str(t_obsv)))
                os.system('cp -r %s.ms %s/%s_%s_Hz_t_obsv_%s_hr.ms'%(vis_file, visibilities_directory, qnt, str(int(frequency[0])), str(t_obsv)))

                img_filename = '%s/%s/%s_%s_Hz_t_obsv_%s_hr'%(images_directory, img_subdirectory[qnt], qnt, str(int(frequency[0])), str(t_obsv))
                make_image_wsclean(ms='%s.ms'%vis_file, imgsize=imgsize, cellsize_arcmin=cellsize_arcmin, img_filename=img_filename)
           
            #Concatenate measurement sets over frequency, for a given quantity and given total observation time
            os.system('rm -rf %s/%s_t_obsv_%s_hr.ms'%(visibilities_directory, qnt, str(t_obsv)))
            os.system('casa --nologger --log2term -c \'import glob; vis=glob.glob("%s/%s_*_Hz_t_obsv_%s_hr.ms"); concat(vis,concatvis="%s/%s_t_obsv_%s_hr.ms")\''%(visibilities_directory, qnt, str(t_obsv), visibilities_directory, qnt, str(t_obsv)))

    #Compute power spectrum
    for t_obsv in total_obsv_time_hr:
        for qnt in quantities:

            os.system('find %s/%s/*%s_hr-image.fits > img.list'%(images_directory, img_subdirectory[qnt], str(t_obsv)))
            os.system('find %s/%s/*%s_hr-psf.fits > psf.list'%(images_directory, img_subdirectory[qnt], str(t_obsv)))

            #Integration time (i) and duration (t) in seconds
            os.system('/home/users/modhurita/ps_eor-0.3.0/simple_ps.py img.list psf.list -i %f -t %f'%(timestep*60, duration*60)) 

            #Save plots
            os.system('cp power_spectra_spatial.eps %s/ps_%s_t_obsv_%s_hr.eps'%(plots_directory, qnt, str(t_obsv)))
            os.system('cp power_spectra_2d.eps %s/ps_%s_t_obsv_%s_hr_2d.eps'%(plots_directory, qnt, str(t_obsv)))
            os.system('cp power_spectra_3d.eps %s/ps_%s_t_obsv_%s_hr_3d.eps'%(plots_directory, qnt, str(t_obsv)))
            os.system('cp variance.eps %s/variance_%s_t_obsv_%s_hr.eps'%(plots_directory, qnt, str(t_obsv)))

            #Save data
            os.system('cp power_spectra_spatial.txt %s/ps_%s_t_obsv_%s_hr.txt'%(data_directory, qnt, str(t_obsv)))
            os.system('cp power_spectra_2d.txt %s/ps_%s_t_obsv_%s_hr_2d.txt'%(data_directory, qnt, str(t_obsv)))
            os.system('cp power_spectra_3d.txt %s/ps_%s_t_obsv_%s_hr_3d.txt'%(data_directory, qnt, str(t_obsv)))
    
    #Copy images and visibilities to respective storage directories
    for qnt in ['eor_p_fg', 'eor_p_noise', 'eor_p_noise_p_fg', 'noise']:
        os.system('cp %s/%s/*%s_hr-{image,psf}.fits %s/images'%(images_directory, img_subdirectory[qnt], str(t_obsv), challenges_directory))
        os.system('cp -r %s/%s_t_obsv*_hr.ms %s/visibilities'%(visibilities_directory, qnt, challenges_directory))

    os.system('python plot_ps.py')

    t2 = time.time()
    print 'Time taken: %f min'%((t2-t1)/60.)
