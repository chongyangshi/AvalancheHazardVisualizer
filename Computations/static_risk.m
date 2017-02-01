% SLOPE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSSlope.tif';
% ASPECT_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSAspects.tif';
% CURVATURE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSCurvature.tif';
% RISK_RASTER = '/media/icydoge/Shared/OS5/MATLAB/WGSStaticRisk.tif';

SLOPE_RASTER = '~/Downloads/WGSSlope.tif';
ASPECT_RASTER = '~/Downloads/WGSAspects.tif';
CURVATURE_RASTER = '~/Downloads/WGSCurvature.tif';
RISK_RASTER = '~/Downloads/WGSStaticRisk.tif';

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
neighbours = zeros(x_min_size, 9);
slope_neighbours = zeros(9, x_min_size);
aspect_neighbours = zeros(9, x_min_size);
work_done = 0;
total_work = y_min_size * x_min_size;
for y = 1:y_min_size
        
    % Slope risk with pre-defined function.
    current_slope_risks = slope_risk(slope_r(y, :));
    
    % Curvature risk with pre-defined function.
    curvatures = curvature_r(y, :);
    curvatures(isnan(curvatures)) = 0;
    current_curvature_risks = curvature_risk(curvatures);
    
    % Repeat sides when getting neighbours.
    for x = 1:x_min_size
        current_position = 1;
        for i = (x-1):(x+1)
            for j = (y-1):(y+1)
                ix = max(1, i);
                ix = min(x_min_size, ix);
                iy = max(1, j);
                iy = min(y_min_size, iy);
                slope_neighbours(current_position, x) = slope_r(iy, ix);
                aspect_neighbours(current_position, x) = aspect_r(iy, ix);
            end
        end
    end
    
    % Now we can get the roughness risk.
    current_roughness_risks = roughness_risk(slope_neighbours, aspect_neighbours);
    
    % Tally them together, currently just a mean (multiply made it too
    % small).
    total_risks = current_slope_risks .* current_curvature_risks .* current_roughness_risks;
    static_risk_r(y, :) = total_risks;
    if max(total_risks) > current_max
        current_max = max(total_risks);
    end
    if min(total_risks) < current_min
        current_min = min(total_risks);
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
