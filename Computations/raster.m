SOURCE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNG.tif';
%TARGET_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNGFittedTest.tif';
ASPECT_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNGAspectsTest.tif';
PARALLEL = 0;
WORKERS = 0;

% Disable warnings.
if PARALLEL == 1
    c = parcluster('local');
    WORKERS = c.NumWorkers;
    parpool;
    pctRunOnAll warning off;
else
    warning off;
end

% Read input raster and initialize.
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_max = size(rst,1) - 1;
y_max = size(rst,2) - 1;
%output = rst;
aspects = zeros(size(rst));

% Start timer.
disp('Surface fittings started...');
tic;

% Use: z = ax^2 + by^2 + cxy + dx + ey + f
% 
% (-1,1)  (0,1)  (1,1)
% (-1,0)  (0,0)  (1,0)
% (-1,-1) (0,-1) (1,-1)
%
coords = [-1 1; 0 1; 1 1; -1 0; 0 0; 1 0; -1 -1; 0 -1; 1 -1];
A(:,1) = coords(:,1).^2;
A(:,2) = coords(:,2).^2;
A(:,3) = coords(:,1).*coords(:,2);
A(:,4) = coords(:,1);
A(:,5) = coords(:,2);
A(:,6) = 1;

% Find neighbours of each point that is not on an edge, and choose the
% points that have all valid neighbours (non-zero), fit a surface for the
% neighbourhood and move the point onto the surface.
parfor_progress(x_max);

parfor (x = 2:x_max, WORKERS) %if WORKERS = 0 as initially set, no parallel.
    for y = 2:y_max
        
        % Pick our neighbours.
        neighbours = pickneighbours(rst, x, y);
        
        % Check that boundaries are valid and no data is 0 (no-data in raster).
        if (any(isnan(neighbours(:))) == 0) && (any(neighbours(:,3)) == 1) 
            
            % Fit and calculate height.
            z = neighbours(:,3);
            C = A\z;
            %output(x,y) = C(6);
            
            % Partial differentials (gradients) are always constant due to 
            % always taking (0,0), this calculates the aspect with 0 
            % degrees being north-facing.
            raw_aspect_value = 180 * atan2(C(5), C(4)) / pi; 
            
            % Store aspect value.
            if raw_aspect_value == 0 % Special case to prevent 270 being 0 degrees.
                aspects(x, y) = 0
            else 
                aspects(x, y) = mod(270-raw_aspect_value, 360);
            end
            % Differentiate to compute gradients and therefore surface
            % normal
            % From normal, infer aspect
            % Aspect = atan2(ny,nx);
            % Slope angle will be to do with nz, theta = acos(nz);
            % ... curvature, convexity...
            
            
        end
        
    end
    parfor_progress;
end

parfor_progress(0);

% Stop timer and report performance.
seconds = toc;
fprintf('Surface fitting completed in %f seconds.\r', seconds);
disp('Purging original input from memory...');
clear rst;
disp('Writing output to the target rasters...');

% Write output rasters.
CoordRefSysCode = 27700; % British National Grid.
%geotiffwrite(TARGET_RASTER, output, raster_info, 'CoordRefSysCode', CoordRefSysCode);
%disp('Output written to the target raster, all done.');
geotiffwrite(ASPECT_RASTER, aspects, raster_info, 'CoordRefSysCode', CoordRefSysCode);
disp('Output written to the aspect raster, all done.');

% Close off.
delete(gcp('nocreate'));
