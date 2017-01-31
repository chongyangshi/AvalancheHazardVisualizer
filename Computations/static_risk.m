SLOPE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSSlope.tif';
ASPECT_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSAspects.tif';
CURVATURE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSCurvature.tif';
RISK_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSStaticRisk.tif';

% Start timer.
disp('Reading rasters...');

% Read input rasters and initialize.
[slope_r, slope_r_info] = geotiffread(SLOPE_RASTER);
[aspect_r, aspect_r_info] = geotiffread(ASPECT_RASTER);
[curvature_r, curvature_r_info] = geotiffread(CURVATURE_RASTER);

% Static risk raster initialisation.
% Sizes of the three input rasters should be identical, but just in case...
x_min_size = min([size(slope_r, 2) size(curvature_r, 2) size(aspect_r, 2)]);
y_min_size = min([size(slope_r, 1) size(curvature_r, 1) size(aspect_r, 1)]);
static_risk_r = zeros(y_min_size, x_min_size);

% Start timer.

disp('Static risk computation started...');
wb = waitbar(0, 'Please wait while static risk is being calculated pixel by pixel...');
tic;

% Calculate static risk.
current_max = 0;
current_min = 1;
slope_neighbours = zeros(9, 1);
aspect_neighbours = zeros(9, 1);
work_done = 0;
total_work = y_min_size * x_min_size;
for y = 1:y_min_size
    for x = 1:x_min_size
        
        % Slope risk with pre-defined function.
        [current_slope_risk, slope_nmz] = slope_risk(slope_r(y, x));
        
        % Curvature risk with pre-defined function.
        [current_curvature_risk, curvature_nmz] = curvature_risk(curvature_r(y, x));
        
        % Repeat sides when getting neighbours.
        current_position = 1;
        for i = (x-1):(x+1)
            for j = (y-1):(y+1)
                ix = max(1, i);
                ix = min(x_min_size, ix);
                iy = max(1, j);
                iy = min(y_min_size, iy);
                slope_neighbours(current_position) = slope_r(iy, ix);
                aspect_neighbours(current_position) = aspect_r(iy, ix);
                current_position = current_position + 1;
            end
        end
        
        % Now we can get the roughness risk.
        [current_roughness_risk, roughness_nmz] = roughness_risk(slope_neighbours, aspect_neighbours);
    
        % Tally them together, currently just a mean (multiply made it too
        % small).
        total_risk = (current_slope_risk / slope_nmz) * (current_curvature_risk / curvature_nmz) * (current_roughness_risk / roughness_nmz);
        static_risk_r(y, x) = total_risk;
        if total_risk > current_max
            current_max = total_risk;
        end
        if total_risk < current_min
            current_min = total_risk;
        end
    end
    work_done = work_done + x_min_size;
    waitbar(work_done / total_work);
end

% Stop timer and report performance.
close(wb);
seconds = toc;
fprintf('Surface fitting completed in %f seconds.\r', seconds);
disp('Purging original inputs from memory...');
clear slope_r;
clear aspect_r;
clear curvature_r;
fprintf('The maximum multiplicative risk is %f, and the minimum multiplicative risk is %f.\n', current_max, current_min);
disp('Writing output to the target rasters...');


% Write output rasters.
CoordRefSysCode = 4326; % WGS           
geotiffwrite(RISK_RASTER, static_risk_r, slope_r_info, 'CoordRefSysCode', CoordRefSysCode);
disp('Output written to the static risk raster, all done.');
